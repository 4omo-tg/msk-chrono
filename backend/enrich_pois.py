import asyncio
from app.db.session import AsyncSessionLocal
from app.models.poi import PointOfInterest as POI
from sqlalchemy import select

async def enrich_pois():
    data = {
        "Румянцевский музей (Дом Пашкова)": {
            "description": "Один из самых знаменитых памятников классицизма в Москве. Построен в 1784—1786 годах по заказу капитан-поручика лейб-гвардии Семеновского полка Петра Егоровича Пашкова. Считается, что проект здания принадлежит великому архитектору Василию Баженову. С 1862 года здесь располагался Румянцевский музей — первый публичный музей Москвы. Именно с террасы Дома Пашкова прощались с Москвой Воланд и его свита в романе Булгакова «Мастер и Маргарита».",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Pashkov_House_19thC.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Moscow_July_2011-3a.jpg"
        },
        "Боровицкая башня": {
            "description": "Угловая башня Московского Кремля, построенная в 1490 году итальянским архитектором Пьетро Антонио Солари. Свое название получила от Боровицкого холма, на котором когда-то рос сосновый бор. Башня имеет уникальную ступенчатую форму. Долгое время она служила хозяйственным въездом в Кремль, а сегодня через её ворота в Кремль традиционно заезжает президентский кортеж.",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Borovitskaya_Tower_19thC.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Borovitskaya_tower.jpg"
        },
        "Старый Каменный мост": {
            "description": "Первый постоянный каменный мост через Москву-реку, известный как Всехсвятский, был достроен в 1692 году. Он был огромным для своего времени сооружением, на нем располагались лавки и даже жилые помещения. К середине XIX века мост сильно обветшал и был заменен металлическим, а в 1938 году был построен современный Большой Каменный мост, который находится чуть выше по течению.",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/8/87/Vsekhsvyatsky_Ston_Bridge_Drawing.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/7/75/Large_Stone_Bridge_2015.jpg"
        },
        "Государственный исторический музей": {
            "description": "Крупнейший национальный исторический музей России, основанный в 1872 году. Здание в псевдорусском стиле было построено по проекту архитектора Владимира Шервуда. Экспозиция музея охватывает историю России с древнейших времен до начала XX века. Внутренние залы музея оформлены в стиле различных исторических эпох и сами по себе являются произведениями искусства.",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/d/df/SHM_Moscow_1900.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/b/b5/State_Historical_Museum_Moscow.jpg"
        },
        "Мавзолей Ленина": {
            "description": "Памятник-усыпальница на Красной площади, где с 1924 года в забальзамированном виде покоится тело Владимира Ленина. Современное каменное здание из красного гранита и лабрадора было построено к 1930 году по проекту Алексея Щусева. Сооружение напоминает древние зиккураты и обладает мощной энергетикой, являясь одним из самых спорных и известных объектов Москвы.",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/7/7c/Wooden_Mausoleum_1924.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/4/43/Lenin_Mausoleum_2010.jpg"
        },
        "ГУМ": {
            "description": "Главный Универсальный Магазин, бывшие Верхние торговые ряды. Построен в 1893 году по проекту Александра Померанцева и инженера Владимира Шухова. Уникальные стеклянные своды Шухова стали прорывом в инженерной мысли того времени. Это не просто магазин, а целый город с внутренними улицами, мостиками и знаменитым фонтаном в центре, где каждый час бьют куранты.",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Upper_Trading_Rows_1893.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/5/52/GUM_Moscow.jpg"
        },
        "Собор Василия Блаженного": {
            "description": "Официально — Собор Покрова Пресвятой Богородицы, что на Рву. Построен Иваном Грозным в 1555—1561 годах в честь взятия Казани. Собор состоит из восьми церквей, окружающих центральную девятую. Согласно легенде, архитекторов Барму и Постника ослепили по приказу царя, чтобы они не могли построить ничего прекраснее, хотя это признано мифом.",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/a/ac/St_Basils_Cathedral_19thC.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/0/01/Saint_Basil%27s_Cathedral_in_Moscow_August_2022_02.jpg"
        },
        "Парк Зарядье": {
            "description": "Современный парк, открытый в 2017 году на месте снесенной гостиницы «Россия». Уникальность парка в создании четырех природных зон России: тундры, степи, леса и болота с искусственным микроклиматом. Главной достопримечательностью является Парящий мост — 70-метровая вылетная консоль над Москвой-рекой без единой опоры. Это место, где будущее встречается с историей древнего квартала Зарядье.",
            "historic_image_url": "https://upload.wikimedia.org/wikipedia/commons/3/30/Hotel_Rossija_1970s.jpg",
            "modern_image_url": "https://upload.wikimedia.org/wikipedia/commons/3/33/Zaryadye_Park_Panorama.jpg"
        }
    }

    async with AsyncSessionLocal() as session:
        for title, info in data.items():
            result = await session.execute(select(POI).where(POI.title == title))
            poi = result.scalars().first()
            if poi:
                poi.description = info["description"]
                poi.historic_image_url = info["historic_image_url"]
                poi.modern_image_url = info["modern_image_url"]
                session.add(poi)
                print(f"Enriched: {title}")
            else:
                print(f"Not found: {title}")
        
        await session.commit()
        print("All POIs enriched successfully.")

if __name__ == "__main__":
    asyncio.run(enrich_pois())
