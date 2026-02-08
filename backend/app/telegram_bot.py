"""Telegram Bot for authentication"""
import secrets
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from app.core.config import settings

# Database connection string (sync version for bot)
DB_URL = settings.DATABASE_URL.replace('+asyncpg', '').replace('postgresql+asyncpg', 'postgresql')

# Site URL for redirect
SITE_URL = "https://test-serv.exe.xyz:8000"


def generate_code() -> str:
    """Generate a 6-digit auth code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def code_exists(code: str) -> bool:
    """Check if code already exists"""
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM telegram_auth_codes WHERE code = %s", (code,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def save_code_to_db(code: str, user_data: dict):
    """Save auth code to database"""
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM telegram_auth_codes WHERE created_at < NOW() - INTERVAL '10 minutes'")
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


def update_auth_session(session_id: str, user_data: dict) -> bool:
    """Update auth session with user data (no code needed)"""
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE telegram_auth_sessions 
            SET telegram_id = %s, 
                telegram_username = %s, 
                telegram_first_name = %s, 
                telegram_photo_url = %s
            WHERE session_id = %s 
              AND created_at > NOW() - INTERVAL '10 minutes'
              AND telegram_id IS NULL
            RETURNING id
        """, (
            user_data['telegram_id'], 
            user_data['username'], 
            user_data['first_name'], 
            user_data['photo_url'],
            session_id
        ))
        result = cur.fetchone()
        conn.commit()
        return result is not None
    finally:
        conn.close()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
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
    
    user_data = {
        'telegram_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'photo_url': photo_url,
    }
    
    # Check if this is a deep link with session_id
    if context.args and len(context.args) > 0:
        session_id = context.args[0]
        
        # Try to update the session
        if update_auth_session(session_id, user_data):
            # Create inline button to return to site
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "\u2705 Вернуться на сайт", 
                    url=f"{SITE_URL}/#/dashboard"
                )]
            ])
            
            await update.message.reply_text(
                f"\U0001F389 <b>Авторизация успешна!</b>\n\n"
                f"Привет, {user.first_name}!\n"
                f"Нажмите кнопку ниже, чтобы вернуться на сайт.",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            return
        else:
            await update.message.reply_text(
                "\u26A0\uFE0F Сессия истекла или уже использована.\n\n"
                "Пожалуйста, начните авторизацию заново на сайте.",
                parse_mode='HTML'
            )
            return
    
    # No session - just welcome message
    await update.message.reply_text(
        "\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
        "Для авторизации перейдите на сайт и нажмите \"Войти через Telegram\".\n\n"
        f"\U0001F517 {SITE_URL}",
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
        "Этот бот используется для авторизации на сайте.\n\n"
        "Для входа:\n"
        f"1. Откройте {SITE_URL}\n"
        "2. Нажмите \"Войти через Telegram\"\n"
        "3. Перейдите в бота и нажмите Start\n"
        "4. Готово! Вы авторизованы.",
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
