"""Seed cosmetics data - titles, frames, badges"""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import Title, ProfileFrame, Badge

# Титулы
TITLES = [
    # Default titles
    {"code": "newbie", "name": "Новичок", "description": "Только начинает свой путь", "color": "gray", "rarity": "common", "unlock_type": "default", "is_default": True},
    
    # Level-based titles
    {"code": "explorer", "name": "Исследователь", "description": "Осваивает новые маршруты", "color": "green", "rarity": "common", "unlock_type": "level", "unlock_value": "3"},
    {"code": "walker", "name": "Путешественник", "description": "Исходил немало дорог", "color": "blue", "rarity": "uncommon", "unlock_type": "level", "unlock_value": "5"},
    {"code": "historian", "name": "Историк", "description": "Знает историю города", "color": "amber", "rarity": "rare", "unlock_type": "level", "unlock_value": "10"},
    {"code": "chronicle_keeper", "name": "Хранитель хроник", "description": "Хранит память о прошлом", "color": "purple", "rarity": "epic", "unlock_type": "level", "unlock_value": "15"},
    {"code": "time_master", "name": "Мастер времени", "description": "Путешествует сквозь эпохи", "color": "pink", "rarity": "legendary", "unlock_type": "level", "unlock_value": "25"},
    
    # Achievement-based titles
    {"code": "first_steps", "name": "Первые шаги", "description": "Сделал первый шаг", "color": "emerald", "rarity": "common", "unlock_type": "achievement", "unlock_value": "first_step"},
    {"code": "quiz_master", "name": "Эрудит", "description": "Мастер квизов", "color": "blue", "rarity": "rare", "unlock_type": "achievement", "unlock_value": "quiz_master"},
    {"code": "completionist", "name": "Перфекционист", "description": "Завершил 5 маршрутов", "color": "orange", "rarity": "epic", "unlock_type": "achievement", "unlock_value": "route_explorer"},
]

# Рамки профиля
FRAMES = [
    # Default
    {"code": "none", "name": "Без рамки", "description": "Простой аватар", "css_class": "ring-2 ring-gray-600", "rarity": "common", "unlock_type": "default", "is_default": True},
    
    # Level-based
    {"code": "bronze", "name": "Бронза", "description": "Бронзовая рамка", "css_class": "ring-4 ring-amber-700", "rarity": "common", "unlock_type": "level", "unlock_value": "3"},
    {"code": "silver", "name": "Серебро", "description": "Серебряная рамка", "css_class": "ring-4 ring-gray-400", "rarity": "uncommon", "unlock_type": "level", "unlock_value": "5"},
    {"code": "gold", "name": "Золото", "description": "Золотая рамка", "css_class": "ring-4 ring-yellow-500", "rarity": "rare", "unlock_type": "level", "unlock_value": "10"},
    {"code": "platinum", "name": "Платина", "description": "Платиновая рамка", "css_class": "ring-4 ring-cyan-400 shadow-lg shadow-cyan-400/30", "rarity": "epic", "unlock_type": "level", "unlock_value": "15"},
    {"code": "diamond", "name": "Бриллиант", "description": "Бриллиантовая рамка", "css_class": "ring-4 ring-purple-500 shadow-lg shadow-purple-500/50 animate-pulse", "rarity": "legendary", "unlock_type": "level", "unlock_value": "25"},
    
    # Special frames
    {"code": "vintage", "name": "Винтаж", "description": "Старинная рамка", "css_class": "ring-4 ring-amber-900 ring-offset-2 ring-offset-amber-200", "rarity": "rare", "unlock_type": "achievement", "unlock_value": "historian"},
    {"code": "moscow", "name": "Москва", "description": "Рамка с символикой Москвы", "css_class": "ring-4 ring-red-600 ring-offset-2 ring-offset-red-200", "rarity": "epic", "unlock_type": "achievement", "unlock_value": "moscow_expert"},
]

# Бейджи
BADGES = [
    # Default badges
    {"code": "new_user", "name": "Новый игрок", "description": "Добро пожаловать!", "icon": "Star", "color": "yellow", "rarity": "common", "unlock_type": "default", "is_default": True},
    
    # Level badges
    {"code": "level_5", "name": "Уровень 5", "description": "Достигнут 5 уровень", "icon": "Award", "color": "blue", "rarity": "uncommon", "unlock_type": "level", "unlock_value": "5"},
    {"code": "level_10", "name": "Уровень 10", "description": "Достигнут 10 уровень", "icon": "Trophy", "color": "amber", "rarity": "rare", "unlock_type": "level", "unlock_value": "10"},
    {"code": "level_20", "name": "Уровень 20", "description": "Достигнут 20 уровень", "icon": "Crown", "color": "purple", "rarity": "epic", "unlock_type": "level", "unlock_value": "20"},
    
    # Achievement badges
    {"code": "first_route", "name": "Первый маршрут", "description": "Завершил первый маршрут", "icon": "Route", "color": "green", "rarity": "common", "unlock_type": "achievement", "unlock_value": "route_starter"},
    {"code": "quiz_genius", "name": "Гений квизов", "description": "Правильно ответил на 50 вопросов", "icon": "BookOpen", "color": "blue", "rarity": "rare", "unlock_type": "achievement", "unlock_value": "quiz_master"},
    {"code": "explorer", "name": "Исследователь", "description": "Посетил 20 точек", "icon": "Compass", "color": "emerald", "rarity": "uncommon", "unlock_type": "achievement", "unlock_value": "local_expert"},
    {"code": "photographer", "name": "Фотограф", "description": "Сделал 10 верификаций", "icon": "Camera", "color": "pink", "rarity": "rare", "unlock_type": "achievement", "unlock_value": "verification_master"},
    
    # Streak badges
    {"code": "streak_7", "name": "Неделя активности", "description": "7 дней подряд", "icon": "Flame", "color": "orange", "rarity": "uncommon", "unlock_type": "achievement", "unlock_value": "streak_week"},
    {"code": "streak_30", "name": "Месяц активности", "description": "30 дней подряд", "icon": "Zap", "color": "red", "rarity": "epic", "unlock_type": "achievement", "unlock_value": "streak_month"},
]


async def seed_cosmetics():
    """Seed all cosmetics data"""
    async with AsyncSessionLocal() as db:
        # Seed titles
        print("Загружаем титулы...")
        for title_data in TITLES:
            existing = await db.scalar(select(Title).where(Title.code == title_data["code"]))
            if not existing:
                title = Title(**title_data)
                db.add(title)
                print(f"  + {title_data['name']}")
        
        # Seed frames
        print("Загружаем рамки...")
        for frame_data in FRAMES:
            existing = await db.scalar(select(ProfileFrame).where(ProfileFrame.code == frame_data["code"]))
            if not existing:
                frame = ProfileFrame(**frame_data)
                db.add(frame)
                print(f"  + {frame_data['name']}")
        
        # Seed badges
        print("Загружаем бейджи...")
        for badge_data in BADGES:
            existing = await db.scalar(select(Badge).where(Badge.code == badge_data["code"]))
            if not existing:
                badge = Badge(**badge_data)
                db.add(badge)
                print(f"  + {badge_data['name']}")
        
        await db.commit()
        print("Готово!")


if __name__ == "__main__":
    asyncio.run(seed_cosmetics())
