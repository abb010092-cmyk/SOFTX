import os
import json
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- НАСТРОЙКА ТОКЕНА ---
TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"

def load_sites():
    try:
        with open("sites.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки базы sites.json: {e}")
        return {}

SITES_DB = load_sites()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡️ **SOFTX OSINT ENGINE v2.5** ⚡️\n\n"
        "Запущен продвинутый асинхронный сканер цифрового следа.\n\n"
        "**Команды:**\n"
        "🔹 `/sherlock [никнейм]` — Поиск аккаунтов по 100+ сайтам.\n"
        "🔹 `/leak [email]` — Проверка почты по базам утечек."
    )

# Улучшенный воркер с фильтрацией "страниц-призраков"
async def check_single_site(session, name, data, username):
    # Исправление синтаксиса на лету, если в базе осталась кривая ссылка
    base_url = data["url"]
    if ".org:{}" in base_url:
        base_url = base_url.replace(".org:{}", ".org/wiki/{}")
    elif ".com:{}" in base_url:
        base_url = base_url.replace(".com:{}", ".com/wiki/{}")
        
    url = base_url.format(username)
    error_type = data.get("error_type", "status_code")

    # Браузерные заголовки, чтобы сайты не понимали, что это скрипт
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        # allow_redirects=False важно, чтобы поймать сайты, кидающие на login/регистрацию
        async with session.get(url, headers=headers, timeout=5, allow_redirects=False) as response:
            
            # Проверка по статус-коду
            if error_type == "status_code":
                if response.status == 200:
                    # Дополнительная проверка контента для предотвращения ложных срабатываний
                    html = await response.text(errors='ignore')
                    low_html = html.lower()
                    
                    # Маркеры того, что профиля на самом деле нет
                    bad_signals = ["content=\"not found\"", "page not found", "профиль не найден", "аккаунт не найден"]
                    if any(signal in low_html for signal in bad_signals):
                        return None
                    return f"✅ {name}: {url}"
                
                # Если сайт перенаправляет (301/302), проверяем куда. 
                # Если на страницу авторизации или главную — значит пользователя нет.
                elif response.status in:
                    location = response.headers.get("Location", "").lower()
                    if "login" in location or "signin" in location or "register" in location:
                        return None

            # Проверка по редиректу (как для Telegram)
            elif error_type == "response_url":
                # Разрешаем редирект для проверки конечной точки
                async with session.get(url, headers=headers, timeout=5, allow_redirects=True) as red_resp:
                    if red_resp.status == 200 and data.get("error_url") not in red_resp.url.human_repr():
                        return f"✅ {name}: {url}"
    except:
        pass
    return None

async def sherlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите цель: `/sherlock username`")
        return

    username = context.args[0].lstrip("@")
    status_msg = await update.message.reply_text(f"🚀 Запущена проверка по {len(SITES_DB)} сайтам для: `@{username}`...")

    # Ограничиваем одновременные соединения, чтобы Termux не падал, а сайты не банили
    connector = aiohttp.TCPConnector(limit=30) 
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_single_site(session, name, data, username) for name, data in SITES_DB.items()]
        results = await asyncio.gather(*tasks)

    found_profiles = [r for r in results if r is not None]

    if found_profiles:
        report = f"🕵️‍♂️ **OSINT ОТЧЕТ ДЛЯ: @{username}**\n\n" + "\n".join(found_profiles)
    else:
        report = f"❌ Активных профилей для юзернейма `@{username}` не найдено."

    # Если отчет слишком длинный, бьем его на части (ограничение ТГ - 4096 символов)
    if len(report) > 4000:
        for x in range(0, len(report), 4000):
            await update.message.reply_text(report[x:x+4000], disable_web_page_preview=True, parse_mode="Markdown")
        await status_msg.delete()
    else:
        await status_msg.edit_text(report, disable_web_page_preview=True, parse_mode="Markdown")

async def leak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите объект: `/leak email@example.com`")
        return

    target = context.args[0]
    status_msg = await update.message.reply_text(f"🔎 Сканируем дампы утечек для `{target}`...")

    # Внимание: для работы leakcheck часто требуется бесплатный API ключ. 
    # Ниже исправлен URL запроса (добавлен пропущенный слеш перед целью)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://leakcheck.net{target}", timeout=7) as response:
                if response.status == 200:
                    res_data = await response.json()
                    if res_data.get("success") and res_data.get("result"):
                        out = f"⚠️ **ОБНАРУЖЕНЫ УТЕЧКИ ДЛЯ {target}:**\n\n"
                        for leak in res_data["result"]:
                            out += f"▪️ Источник: `{leak.get('line')}`\n"
                        out += "\n🔒 Данные скомпрометированы. Рекомендуется сменить пароли."
                    else:
                        out = f"✅ Объект `{target}` в публичных базах утечек не обнаружен."
                else:
                    out = "❌ Сервис проверки утечек временно недоступен."
        except Exception as e:
            out = f"❌ Ошибка при запросе к базе: {str(e)}"

    await status_msg.edit_text(out, parse_mode="Markdown")

def main():
    if TOKEN == "ВАШ_ТОКЕН_ОТ_BOTFATHER":
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Вы забыли вставить токен вашего бота!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sherlock", sherlock_command))
    app.add_handler(CommandHandler("leak", leak_command))

    print("🔥 SOFTX OSINT ENGINE запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
