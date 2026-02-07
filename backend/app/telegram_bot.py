"""Telegram Bot for authentication codes"""
import asyncio
import secrets
import time
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from app.core.config import settings

# Store auth codes: {code: {telegram_id, username, first_name, photo_url, created_at}}
auth_codes: dict = {}

# Clean old codes periodically (older than 10 minutes)
CODE_EXPIRY = 600  # 10 minutes


def generate_code() -> str:
    """Generate a 6-digit auth code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def cleanup_old_codes():
    """Remove expired codes"""
    now = time.time()
    expired = [code for code, data in auth_codes.items() if now - data['created_at'] > CODE_EXPIRY]
    for code in expired:
        del auth_codes[code]


def get_and_consume_code(code: str) -> dict | None:
    """Get code data and remove it (one-time use)"""
    cleanup_old_codes()
    if code in auth_codes:
        data = auth_codes.pop(code)
        return data
    return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - generate auth code"""
    user = update.effective_user
    
    # Generate unique code
    code = generate_code()
    while code in auth_codes:
        code = generate_code()
    
    # Get user photo URL
    photo_url = None
    try:
        photos = await user.get_profile_photos(limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]  # Get largest size
            file = await context.bot.get_file(photo.file_id)
            photo_url = file.file_path
    except Exception:
        pass
    
    # Store code with user data
    auth_codes[code] = {
        'telegram_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'photo_url': photo_url,
        'created_at': time.time()
    }
    
    await update.message.reply_text(
        f"🔐 Ваш код для входа на сайт:\n\n"
        f"<code>{code}</code>\n\n"
        f"Введите этот код на сайте для авторизации.\n"
        f"Код действителен 10 минут.",
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "🏛 <b>Moscow Chrono Walker</b>\n\n"
        "Этот бот используется для авторизации на сайте.\n\n"
        "Команды:\n"
        "/start - Получить код для входа\n"
        "/help - Показать эту справку",
        parse_mode='HTML'
    )


def run_bot():
    """Run the telegram bot"""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set, bot not started")
        return
    
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    print(f"Starting Telegram bot @{settings.TELEGRAM_BOT_USERNAME}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
