"""Telegram Bot for authentication (aiogram 3)"""
import asyncio
import logging

import psycopg2
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection string (sync version for bot)
DB_URL = settings.DATABASE_URL.replace('+asyncpg', '').replace('postgresql+asyncpg', 'postgresql')

# Site URL from config
SITE_URL = settings.SITE_URL

router = Router()


# ── DB helpers ──────────────────────────────────────────────

def check_user_exists(telegram_id: int) -> bool:
    conn = psycopg2.connect(DB_URL)
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM "user" WHERE telegram_id = %s', (telegram_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def update_auth_session(session_id: str, user_data: dict) -> bool:
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
            session_id,
        ))
        result = cur.fetchone()
        conn.commit()
        return result is not None
    finally:
        conn.close()


def get_session_status(session_id: str) -> str:
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


# ── Helpers ─────────────────────────────────────────────────

async def get_user_data(bot: Bot, user) -> dict:
    photo_url = None
    try:
        photos = await bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]
            file = await bot.get_file(photo.file_id)
            photo_url = file.file_path
    except Exception:
        pass

    return {
        'telegram_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'photo_url': photo_url,
    }


# ── Handlers ────────────────────────────────────────────────

@router.message(CommandStart(deep_link=True))
async def start_deep_link(message: Message, bot: Bot):
    """Handle /start with deep-link session_id."""
    user = message.from_user
    session_id = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if not session_id:
        return await start_no_link(message)

    status = get_session_status(session_id)

    if status in ('not_found', 'expired'):
        await message.answer(
            "\u26A0\uFE0F <b>Сессия истекла</b>\n\n"
            "Пожалуйста, начните авторизацию заново на сайте.",
            parse_mode=ParseMode.HTML,
        )
        return

    if status == 'used':
        await message.answer(
            "\u2705 <b>Вы уже авторизованы</b>\n\n"
            "Вернитесь на сайт — вход выполнен.",
            parse_mode=ParseMode.HTML,
        )
        return

    user_exists = check_user_exists(user.id)
    btn_text = "\u2705 Войти" if user_exists else "\u2705 Зарегистрироваться и войти"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, callback_data=f"auth:{session_id}")]
    ])

    await message.answer(
        f"\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
        f"Привет, {user.first_name}!\n\n"
        f"Нажмите кнопку ниже для авторизации:",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


@router.message(CommandStart())
async def start_no_link(message: Message):
    """Handle plain /start (no deep link)."""
    await message.answer(
        "\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
        "Для авторизации перейдите на сайт и нажмите \"Войти через Telegram\".\n\n"
        f"\U0001F517 {SITE_URL}",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "\U0001F3DB <b>Moscow Chrono Walker</b>\n\n"
        "Этот бот используется для авторизации на сайте.\n\n"
        "<b>Как войти:</b>\n"
        f"1. Откройте {SITE_URL}\n"
        "2. Нажмите \"Войти через Telegram\"\n"
        "3. В боте нажмите кнопку \"Войти\"\n"
        "4. Готово!",
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("auth:"))
async def auth_callback(callback: CallbackQuery, bot: Bot):
    await callback.answer()

    session_id = callback.data[5:]  # strip "auth:"
    user = callback.from_user

    user_data = await get_user_data(bot, user)

    if update_auth_session(session_id, user_data):
        await callback.message.edit_text(
            f"\U0001F389 <b>Готово!</b>\n\n"
            f"{user.first_name}, вы успешно авторизованы.\n"
            f"Вернитесь на сайт — вход выполнен автоматически.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await callback.message.edit_text(
            "\u26A0\uFE0F <b>Сессия истекла</b>\n\n"
            "Пожалуйста, начните авторизацию заново на сайте.",
            parse_mode=ParseMode.HTML,
        )


# ── Entry point ─────────────────────────────────────────────

async def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set, bot not started")
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting Telegram bot @%s", settings.TELEGRAM_BOT_USERNAME)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def run_bot():
    asyncio.run(main())


if __name__ == "__main__":
    run_bot()
