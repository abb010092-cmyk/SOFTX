

import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 Добро пожаловать в SOFTX!\n\n"
        "Твой помощник по поиску открытых профилей.\n\n"
        "Команды:\n"
        "/check username — поиск профилей\n"
        "/help — помощь"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "SOFTX OSINT Assistant\n\n"
        "Используй:\n"
        "/check username\n\n"
        "Поиск ограничен общедоступными профилями."
    )


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Укажи никнейм: /check username"
        )
        return

    username = context.args[0].lstrip("@")

    if not username.replace("_", "").isalnum():
        await update.message.reply_text("Некорректный username.")
        return

    sites = [
        ("Instagram", f"https://www.instagram.com/{username}/"),
        ("TikTok", f"https://www.tiktok.com/@{username}"),
        ("Telegram", f"https://t.me/{username}"),
        ("ВКонтакте", f"https://vk.com/{username}"),
        ("YouTube", f"https://www.youtube.com/@{username}"),
        ("Reddit", f"https://www.reddit.com/user/{username}/"),
        ("Facebook", f"https://www.facebook.com/{username}")
    ]

    result = f"🔎 SOFTX: {username}\n\n"
    result += "Возможные публичные профили:\n\n"

    for name, url in sites:
        result += f"🌐 {name}: {url}\n"

    result += (
        "\n⚠️ Ссылки сформированы по никнейму, "
        "но существование профилей не подтверждено."
    )

    await update.message.reply_text(result)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check))

    print("SOFTX is running!")
    app.run_polling()


if __name__ == "__main__":
    main()

    if not context.args:
        await update.message.reply_text(
            "Укажи никнейм: /check username"
        )
        return

    username = context.args[0].lstrip("@")

    if not username.replace("_", "").isalnum():
        await update.message.reply_text("Некорректный username.")
        return

    sites = [
        ("GitHub", f"https://github.com/{username}"),
        ("Reddit", f"https://www.reddit.com/user/{username}/"),
        ("Pinterest", f"https://www.pinterest.com/{username}/"),
        ("Instagram", f"https://www.instagram.com/{username}/")
    ]

    result = f"🔎 SOFTX: {username}\n\n"
    result += "Ссылки для проверки публичных профилей:\n\n"

    for name, url in sites:
        result += f"🌐 {name}: {url}\n"

    result += "\nСсылки ещё не проверены на существование."

    await update.message.reply_text(result)

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check))

    print("SOFTX is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
