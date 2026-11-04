import os
import json
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- НАСТРОЙКА ТОКЕНА ---
TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"

# Функция автоматической загрузки базы сайтов из файла sites.json
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
        "⚡️ **SOFTX OSINT ENGINE v2.0** ⚡️\n\n"
        "Запущен полноценный асинхронный сканер цифрового следа.\n\n"
        "**Команды:**\n"
        "🔹 `/sherlock [никнейм]` — Полный глубокий пробив по базе из 100+ сайтов.\n"
        "🔹 `/leak [email]` — Быстрая проверка почты по базам утечек паролей."
    )

# Асинхронный воркер для мгновенной параллельной проверки сайта
async def check_single_site(session, name, data, username):
    url = data["url"].format(username)
    error_type = data.get("error_type", "status_code")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with session.get(url, headers=headers, timeout=6, allow_redirects=True) as response:
            if error_type == "status_code":
                if response.status == 200 and not "error" in response.url.human_repr().lower():
                    return f"✅ {name}: {url}"
            elif error_type == "response_url":
                if response.status == 200 and data.get("error_url") not in response.url.human_repr():
                    return f"✅ {name}: {url}"
    except:
        pass
    return None

# --- МОДУЛЬ 1: АНАЛОГ SHERLOCK (100+ СТАЙТОВ ОДНОВРЕМЕННО) ---
async def sherlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите цель: `/sherlock username`")
        return
        
    username = context.args[0].lstrip("@")
    status_msg = await update.message.reply_text(f"🚀 Запущена параллельная проверка по {len(SITES_DB)} сайтам для: `@{username}`...")
    
    # Запускаем одновременный опрос всех сайтов в один миг
    async with aiohttp.ClientSession() as session:
        tasks = [check_single_site(session, name, data, username) for name, data in SITES_DB.items()]
        results = await asyncio.gather(*tasks)
        
    found_profiles = [r for r in results if r is not None]
    
    if found_profiles:
        report = f"🕵️‍♂️ **OSINT ОТЧЕТ ДЛЯ: @{username}**\n\n" + "\n".join(found_profiles)
    else:
        report = f"❌ Активных профилей для юзернейма `@{username}` не найдено."
        
    await status_msg.edit_text(report, disable_web_page_preview=True, parse_mode="Markdown")

# --- МОДУЛЬ 2: ПОИСК УТЕЧЕК (LEAKCHECK) ---
async def leak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите объект: `/leak email@example.com`")
        return
        
    target = context.args[0]
    status_msg = await update.message.reply_text(f"🔎 Сканируем дампы утечек для `{target}`...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://leakcheck.net{target}", timeout=7) as response:
                if response.status == 200:
                    res_data = await response.json()
                    if res_data.get("success") and res_data.get("result"):
                        out = f"⚠️ **ОБНАРУЖЕНЫ УТЕЧКИ ДЛЯ {target}:**\n\n"
                        for leak in res_data["result"]:
                            out += f"▪️ База данных: `{leak.get('line')}` (Дата: {leak.get('date', 'н/д')})\n"
                        out += "\n🔒 Пароли от этого email скомпрометированы. Рекомендуется их смена."
                    else:
                        out = f"✅ Объект `{target}` в базах утечек не обнаружен."
                else:
                    out = "❌ Публичное API LeakCheck перегружено. Попробуйте позже."
        except Exception as e:
            out = f"❌ Ошибка при запросе к базе: {str(e)}"
            
    await status_msg.edit_text(out, parse_mode="Markdown")

def main():
    if TOKEN == "ВАШ_ТОКЕН_ОТ_BOTFATHER":
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Вы забыли вставить токен вашего бота в строку 9!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sherlock", sherlock_command))
    app.add_handler(CommandHandler("leak", leak_command))
    
    print("🔥 SOFTX OSINT ENGINE запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
