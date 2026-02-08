# 🚀 Развёртывание Moscow Chrono Walker

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone <repository-url>
cd MoscowWalker
```

### 2. Настройте конфигурацию

```bash
cp .env.example .env
```

Отредактируйте `.env` и заполните **обязательные** переменные:

| Переменная | Описание | Как получить |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | Создайте бота у [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_BOT_USERNAME` | Username бота (без @) | Выбираете при создании бота |
| `SECRET_KEY` | Секрет для JWT | `openssl rand -hex 32` |

### 3. Запустите

```bash
docker compose up -d --build
```

Приложение будет доступно на **http://localhost:8000**

---

## 📝 Все переменные окружения

### Обязательные

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USERNAME=my_moscow_bot

# JWT Secret (min 32 символа)
SECRET_KEY=your_super_secret_random_string_here
```

### Опциональные

```env
# AI API для верификации фото чекпоинтов
AI_API_BASE_URL=https://ai-proxxy.exe.xyz/api
AI_API_KEY=                # если нужен ключ
AI_MODEL=qwen3-vl-plus

# URL сайта (для ссылок в TG боте)
SITE_URL=https://your-domain.com

# База данных (по умолчанию настроена для Docker)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=moscow_chrono
```

---

## 🔧 Создание Telegram бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Введите имя бота (например: "Moscow Chrono Walker")
4. Введите username (например: `moscow_chrono_bot`)
5. Скопируйте токен в `TELEGRAM_BOT_TOKEN`
6. Укажите username в `TELEGRAM_BOT_USERNAME` (без @)

Опционально настройте бота:
- `/setdescription` - описание бота
- `/setabouttext` - текст "About"
- `/setuserpic` - аватар бота

---

## 📦 Что разворачивается

Docker Compose запускает 3 сервиса:

| Сервис | Описание | Порт |
|---------|----------|------|
| `db` | PostgreSQL + PostGIS | 5432 (внутренний) |
| `backend` | FastAPI + Svelte frontend | **8000** |
| `telegram-bot` | Telegram бот для авторизации | - |

---

## 🔍 Полезные команды

```bash
# Запуск
docker compose up -d --build

# Просмотр логов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f telegram-bot

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Остановка с удалением данных
docker compose down -v
```

---

## 🌐 Продакшн настройки

Для продакшна рекомендуется:

1. **Измените пароль БД**:
   ```env
   POSTGRES_PASSWORD=strong_random_password
   ```

2. **Установите SITE_URL**:
   ```env
   SITE_URL=https://your-domain.com
   ```

3. **Настройте reverse proxy** (nginx/Caddy) с HTTPS

---

## ❓ Troubleshooting

### "Сессия истекла" в Telegram
- Проверьте что `TELEGRAM_BOT_TOKEN` и `TELEGRAM_BOT_USERNAME` совпадают
- Перезапустите бот: `docker compose restart telegram-bot`

### Бот не запускается
- Проверьте логи: `docker compose logs telegram-bot`
- Убедитесь что токен валидный

### Ошибка подключения к БД
- Проверьте что `db` сервис запущен: `docker compose ps`
- Посмотрите логи: `docker compose logs db`
