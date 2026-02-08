"""Telegram Bot for authentication"""
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from app.core.config import settings

# Database connection string (sync version for bot)
DB_URL = settings.DATABASE_URL.replace('+asyncpg', '').replace('postgresql+asyncpg', 'postgresql')

# Site URL from config
SITE_URL = settings.SITE_URL


def check_user_exists(telegram_id: int) -> bool:
    """Check if user with this telegram_id already exists"""
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM "user" WHERE telegram_id = %s', (telegram_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def update_auth_session(session_id: str, user_data: dict) -> bool:
    """Update auth session with user data"""
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


def get_session_status(session_id: str) -> str:
    """Get session status: 'valid', 'used', 'expired', 'not_found'"""
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT telegram_id, created_at > NOW() - INTERVAL '10 minutes' as valid
            FROM telegram_auth_sessions 
            WHERE session_id = %s
        """, (session_id,))
        row = cur.fetchone()
        if not row:
            return 'not_found'
        telegram_id, valid = row
        if not valid:
            return 'expired'
        if telegram_id:
            return 'used'
        return 'valid'
    finally:
        conn.close()


async def get_user_data(user, context) -> dict:
    """Get user data including photo URL"""
    photo_url = None
    try:
        photos = await user.get_profile_photos(limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]
            file = await context.bot.get_file(photo.file_id)
            photo_url = file.file_path
    except Exception:
        pass
    
    return {
        'telegram_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'photo_url': photo_url,
    }


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show auth button"""
    user = update.effective_user
    
    # Check if this is a deep link with session_id
    if context.args and len(context.args) > 0:
        session_id = context.args[0]
        
        # Check session status
        status = get_session_status(session_id)
        
        if status == 'not_found' or status == 'expired':
            await update.message.reply_text(
                "\u26A0\uFE0F <b>Сессия истекла</b>\n\n"
                "Пожалуйста, начните авторизацию заново на сайте.",
                parse_mode='HTML'
            )
            return
        
        if status == 'used':
            await update.message.reply_text(
                "\u2705 <b>Вы уже авторизованы</b>\n\n"
                "Вернитесь на сайт - вход выполнен.",
                parse_mode='HTML'
            )
            return
        
        # Session is valid - show auth button
        user_exists = check_user_exists(user.id)
        button_text = "\u2705 Войти" if user_exists else "\u2705 Зарегистрироваться и войти"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(button_text, callback_data=f"auth:{session_id}")]
        ])
        
        await update.message.reply_text(
            f"\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
            f"Привет, {user.first_name}!\n\n"
            f"Нажмите кнопку ниже для авторизации:",
            parse_mode='HTML',
            reply_markup=keyboard
        )
        return
    
    # No session - just welcome message
    await update.message.reply_text(
        "\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
        "Для авторизации перейдите на сайт и нажмите \"Войти через Telegram\".\n\n"
        f"\U0001F517 {SITE_URL}",
        parse_mode='HTML'
    )


async def auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle auth button click"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith("auth:"):
        return
    
    session_id = data[5:]  # Remove "auth:" prefix
    user = update.effective_user
    
    # Get user data
    user_data = await get_user_data(user, context)
    
    # Try to update session
    if update_auth_session(session_id, user_data):
        await query.edit_message_text(
            f"\U0001F389 <b>Готово!</b>\n\n"
            f"{user.first_name}, вы успешно авторизованы.\n"
            f"Вернитесь на сайт - вход выполнен автоматически.",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "\u26A0\uFE0F <b>Сессия истекла</b>\n\n"
            "Пожалуйста, начните авторизацию заново на сайте.",
            parse_mode='HTML'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
        "Этот бот используется для авторизации на сайте.\n\n"
        "<b>Как войти:</b>\n"
        f"1. Откройте {SITE_URL}\n"
        "2. Нажмите \"Войти через Telegram\"\n"
        "3. В боте нажмите кнопку \"Войти\"\n"
        "4. Готово!",
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
    application.add_handler(CallbackQueryHandler(auth_callback, pattern="^auth:"))
    
    print(f"Starting Telegram bot @{settings.TELEGRAM_BOT_USERNAME}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
