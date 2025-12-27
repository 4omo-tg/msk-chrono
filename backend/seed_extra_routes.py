import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route
from app.models.poi import PointOfInterest as POI

async def seed_new_routes():
    async with AsyncSessionLocal() as session:
        print("Seeding new routes...")

        # --- Route 2: Mystical Moscow (Bulgakov) ---
        route_bulgakov = Route(
            title="Мистическая Москва",
            description="Прогулка по местам романа 'Мастер и Маргарита' и другим мистическим уголкам столицы. Узнайте тайны Патриарших и нехорошей квартиры.",
            difficulty="medium",
            reward_xp=800,
            is_premium=False
        )

        # ... (Points remain same) ...

        # --- Route 3: Golden Zamoskvorechye ---
        route_gold = Route(
            title="Золотое Замоскворечье",
            description="Путешествие по купеческому району Москвы с его уютными улочками, древними храмами и панорамными видами на Кремль.",
            difficulty="easy",
            reward_xp=1000,
            is_premium=True
        )
        
        pois_bulgakov = [
            POI(
                title="Патриаршие пруды",
                description="Место, где началась история Мастера и Маргариты. 'Однажды весною, в час небывало жаркого заката...'",
                latitude=55.7637, longitude=37.5925,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Patriarch_Ponds_2017.jpg/800px-Patriarch_Ponds_2017.jpg"
            ),
            POI(
                title="Дом Пигита (Нехорошая квартира)",
                description="Знаменитый дом 302-бис по Садовой, где располагалась 'Нехорошая квартира' №50.",
                latitude=55.7669, longitude=37.5927,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Bolshaya_sadovaya_10_2009.JPG/800px-Bolshaya_sadovaya_10_2009.JPG"
            ),
            POI(
                title="Театр Варьете (Театр Сатиры)",
                description="Место проведения сеанса черной магии с разоблачением.",
                latitude=55.7675, longitude=37.5938,
                 modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Moscow_Satire_Theatre_Facade.jpg/800px-Moscow_Satire_Theatre_Facade.jpg"
            ),
            POI(
                title="Сад Аквариум",
                description="Старинный сад, где Варенуха встретился с Бегемотом и Азазелло.",
                latitude=55.7670, longitude=37.5950,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/d/d0/Aquarium_Garden_Moscow.jpg"
            ),
            POI(
                title="Дом Грибоедова (Литературный институт)",
                description="Дом МАССОЛИТа, где Берлиоз не успел на заседание.",
                latitude=55.7628, longitude=37.6015,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/A._Herzen_house_Moscow.jpg/800px-A._Herzen_house_Moscow.jpg"
            ),
            POI(
                title="Тверской бульвар",
                description="Старейший бульвар Москвы, упоминаемый во множестве литературных произведений.",
                latitude=55.7600, longitude=37.6030,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Tverskoy_boulevard_in_Moscow_02.jpg/800px-Tverskoy_boulevard_in_Moscow_02.jpg"
            ),
            POI(
                title="Пушкинская площадь",
                description="Сердце литературной Москвы памятник А.С. Пушкину.",
                latitude=55.7655, longitude=37.6055,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Pushkin_Square_Moscow.jpg/800px-Pushkin_Square_Moscow.jpg"
            ),
            POI(
                title="Дом Нирнзее",
                description="Первый московский 'тучерез' (небоскреб), связанный с булгаковскими героями.",
                latitude=55.7645, longitude=37.6020,
                 modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Nirnsee_House_2011.jpg/800px-Nirnsee_House_2011.jpg"
            ),
            POI(
                title="МХАТ им. Горького",
                description="Театр, где Булгаков работал ассистентом режиссера и где ставились его пьесы.",
                latitude=55.7605, longitude=37.6035,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Moscow_Art_Theatre_Gorky.jpg/800px-Moscow_Art_Theatre_Gorky.jpg"
            ),
            POI(
                title="Особняк Рябушинского",
                description="Шедевр модерна, где жил Максим Горький. Булгаков здесь бывал.",
                latitude=55.7585, longitude=37.5975,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Ryabushinsky_House_2010.jpg/800px-Ryabushinsky_House_2010.jpg"
            )
        ]

        # Add POIs to route
        for poi in pois_bulgakov:
            route_bulgakov.points.append(poi)





        pois_gold = [
            POI(
                title="Чугунный мост",
                description="Старт маршрута. Живописный мост через Водоотводный канал.",
                latitude=55.7480, longitude=37.6320,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Chugunny_Bridge_Moscow.jpg/800px-Chugunny_Bridge_Moscow.jpg"
            ),
            POI(
                title="Церковь Климента Папы Римского",
                description="Величественный барочный храм, шедевр архитектуры Замоскворечья.",
                latitude=55.7415, longitude=37.6290,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Church_of_St._Clement_Moscow.jpg/800px-Church_of_St._Clement_Moscow.jpg"
            ),
            POI(
                title="Третьяковская галерея",
                description="Главный музей русского искусства в историческом здании.",
                latitude=55.7415, longitude=37.6205,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Tretyakov_Gallery_Main_Building.jpg/800px-Tretyakov_Gallery_Main_Building.jpg"
            ),
            POI(
                title="Фонтан Искусств",
                description="Красивый фонтан в сквере рядом с Третьяковской галереей.",
                latitude=55.7410, longitude=37.6210,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Fountain_of_Arts_Moscow.jpg/800px-Fountain_of_Arts_Moscow.jpg"
            ),
            POI(
                title="Марфо-Мариинская обитель",
                description="Обитель милосердия, созданная Великой княгиней Елизаветой Федоровной. Архитектор Щусев.",
                latitude=55.7395, longitude=37.6225,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Marfo-Mariinsky_Convent_Katholikon.jpg/800px-Marfo-Mariinsky_Convent_Katholikon.jpg"
            ),
            POI(
                title="Кадашевская слобода",
                description="Историческая местность с прекрасным храмом Воскресения Христова.",
                latitude=55.7435, longitude=37.6220,
                 modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Kadashi_Church.jpg/800px-Kadashi_Church.jpg"
            ),
            POI(
                title="Болотная площадь",
                description="Место исторических событий и народных гуляний, парк и скульптуры Шемякина.",
                latitude=55.7450, longitude=37.6180,
                 modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Bolotnaya_Square.jpg/800px-Bolotnaya_Square.jpg"
            ),
            POI(
                title="Дом на Набережной",
                description="Легендарный дом правительства, памятник конструктивизма с трагической историей.",
                latitude=55.7445, longitude=37.6130,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/House_on_Embankment.jpg/800px-House_on_Embankment.jpg"
            ),
            POI(
                title="Патриарший мост",
                description="Пешеходный мост с лучшими видами на Кремль и Храм Христа Спасителя.",
                latitude=55.7425, longitude=37.6085,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Patriarch_Bridge_Moscow.jpg/800px-Patriarch_Bridge_Moscow.jpg"
            ),
            POI(
                title="ГЭС-2",
                description="Новое культурное пространство в здании бывшей электростанции.",
                latitude=55.7410, longitude=37.6105,
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/GES-2_Moscow.jpg/800px-GES-2_Moscow.jpg"
            )
        ]
        
        for poi in pois_gold:
            route_gold.points.append(poi)

        session.add(route_bulgakov)
        session.add(route_gold)
        
        await session.commit()
        print("Successfully added 2 new routes with 20 POIs!")

if __name__ == "__main__":
    asyncio.run(seed_new_routes())
