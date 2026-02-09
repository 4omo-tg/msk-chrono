#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Creating Telegram auth tables..."
python -c "
import psycopg2, os
db_url = os.environ['DATABASE_URL'].replace('+asyncpg', '').replace('postgresql+asyncpg', 'postgresql')
conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS telegram_auth_sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR NOT NULL UNIQUE,
        telegram_id BIGINT,
        telegram_username VARCHAR,
        telegram_first_name VARCHAR,
        telegram_photo_url VARCHAR,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS telegram_auth_codes (
        id SERIAL PRIMARY KEY,
        code VARCHAR NOT NULL UNIQUE,
        telegram_id BIGINT NOT NULL,
        telegram_username VARCHAR,
        telegram_first_name VARCHAR,
        telegram_photo_url VARCHAR,
        created_at TIMESTAMP DEFAULT NOW()
    );
''')
conn.commit()
conn.close()
print('Telegram auth tables OK')
" || true

echo "Seeding cosmetics data..."
python -m seed_cosmetics

echo "Seeding initial data..."
python -c "
import asyncio
from app.initial_data import init_db
try:
    asyncio.run(init_db())
except Exception as e:
    print(f'Seed data note: {e}')
" || true

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
