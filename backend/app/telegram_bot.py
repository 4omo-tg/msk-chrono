"""Telegram Bot for authentication codes"""
import asyncio
import secrets
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.core.config import settings

# Database connection string (sync version for bot)
DB_URL = settings.DATABASE_URL.replace('+asyncpg', '').replace('postgresql+asyncpg', 'postgresql')


def generate_code() -> str:
    """Generate a 6-digit auth code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def save_code_to_db(code: str, user_data: dict):
    """Save auth code to database"""
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        # Clean old codes (older than 10 minutes)
        cur.execute("DELETE FROM telegram_auth_codes WHERE created_at < NOW() - INTERVAL '10 minutes'")
        # Insert new code
        cur.execute("""
            INSERT INTO telegram_auth_codes (code, telegram_id, telegram_username, telegram_first_name, telegram_photo_url)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                telegram_id = EXCLUDED.telegram_id,
                telegram_username = EXCLUDED.telegram_username,
                telegram_first_name = EXCLUDED.telegram_first_name,
                telegram_photo_url = EXCLUDED.telegram_photo_url,
                created_at = NOW()
        """, (code, user_data['telegram_id'], user_data['username'], user_data['first_name'], user_data['photo_url']))
        conn.commit()
    finally:
        conn.close()


def code_exists(code: str) -> bool:
    """Check if code already exists"""
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM telegram_auth_codes WHERE code = %s", (code,))
        return cur.fetchone() is not None
    finally:
        conn.close()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - generate auth code"""
    user = update.effective_user
    
    # Generate unique code
    code = generate_code()
    attempts = 0
    while code_exists(code) and attempts < 10:
        code = generate_code()
        attempts += 1
    
    # Get user photo URL
    photo_url = None
    try:
        photos = await user.get_profile_photos(limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]
            file = await context.bot.get_file(photo.file_id)
            photo_url = file.file_path
    except Exception:
        pass
    
    # Save code to database
    user_data = {
        'telegram_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'photo_url': photo_url,
    }
    save_code_to_db(code, user_data)
    
    await update.message.reply_text(
        f"\U0001F510 Ваш код для входа на сайт:\n\n"
        f"<code>{code}</code>\n\n"
        f"Введите этот код на сайте для авторизации.\n"
        f"Код действителен 10 минут.",
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
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
