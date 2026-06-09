from aiogram.filters.command import Command
from aiogram import Router, types, F
WEATHER_KEY = 'https://api.open-meteo.com/v1/forecast'
WEATHER_KEY2 = 'https://geocoding-api.open-meteo.com/v1/search'
DB_NAME = 'recent_cities.sql'
url_nomination = 'https://nominatim.openstreetmap.org/reverse'
import tg_bot_folder.keybord as keybord

import aiohttp
import aiosqlite
import datetime



router = Router()
in_input_city = False

async def cmd_start(message: types.Message):
    await message.answer(f"Привет {message.from_user.first_name}! Я бот о погоде. Отправь мне свой город и я покажу погоду.", reply_markup=keybord.main)


async def city_by_coordinats(message: types.Message):
    params_nomination = {'format': 'json', 'lat': message.location.latitude, 'lon': message.location.longitude, 'accept-language': 'ru-RU', 'email': 'pvzrus2@gmail.com'}
    async with aiohttp.ClientSession(headers={'User-Agent': 'MyWeatherBot/1.0 pvzrus2@gmail.com'}) as session:
        async with session.get(url_nomination, params=params_nomination) as response:

            if response.status == 200:
                data_nomination = await response.json()
                city = data_nomination.get('display_name', '')
                city = city.split(',')
                city = city[3]
                city = city.strip()
                return city
            else:
                print(f'api error: {response.status}')



async def check_coordinats(message: types.Message):
    global in_input_city
    in_input_city = False
    user_id = message.from_user.id
    my_latitude = message.location.latitude
    my_longitude = message.location.longitude
    time = datetime.datetime.now().isoformat()
    city = await city_by_coordinats(message)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO users (user_id, latitude_db, longitude_db, time_db, cities_db) VALUES(?,?,?,?,?)', (user_id, my_latitude, my_longitude, time, city))
        await db.commit()



    async with aiohttp.ClientSession() as session:
        my_params = {'latitude': my_latitude, 'longitude': my_longitude, 'timezone': 'auto', 'hourly': 'temperature_2m'}

        async with session.get(WEATHER_KEY, params=my_params) as response:
            if response.status == 200:
                my_data = await response.json()
                current_temp = my_data['hourly']['temperature_2m'][0]

                await message.answer(f'Температура сейчас: {current_temp}°C \n' 
                                     f'На координаты: {my_latitude}, {my_longitude}\n'
                                     f'В городе: {city}')
            else:
                await message.answer('Что то не так')


async def input_city(message: types.Message):
    global in_input_city
    in_input_city = True
    await message.answer('Введи любой город!')

async def send_input_city(message: types.Message):
    if in_input_city:
        async with aiohttp.ClientSession() as session:
            id_user = message.from_user.id
            city_user = message.text
            time = datetime.datetime.now().isoformat()
            my_params = {'name': city_user, 'language': 'ru', 'format': 'json'}
            async with session.get(WEATHER_KEY2, params=my_params) as response:
                if response.status == 200:
                    my_data = await response.json()
                    first_element = my_data['results'][0]
                    my_params = {'latitude': first_element['latitude'], 'longitude': first_element['longitude'], 'timezone': 'auto',
                                 'hourly': 'temperature_2m'}

                    async with aiosqlite.connect(DB_NAME) as db:
                        await db.execute('INSERT INTO users(user_id, latitude_db, longitude_db, time_db, cities_db) VALUES(?,?,?,?,?)', (id_user, first_element['latitude'], first_element['longitude'], time, first_element['name']))
                        await db.commit()

                    async with session.get(WEATHER_KEY, params=my_params) as response:
                        if response.status == 200:
                            my_data2 = await response.json()
                            current_temp = my_data2['hourly']['temperature_2m'][0]
                            print(my_data2)
                            await message.answer(f'Температура сейчас: {current_temp}°C \n'
                                                 f'На координаты: {first_element['latitude']}, {first_element['longitude']}\n'
                                                 f'В городе: {first_element['name']}')
                        else:
                            print(f'api error: {response.status}')
                            await message.answer("Что то не тк")

                else:
                    await message.answer('Что то не так')
    else:
        await message.answer('Сначала нужно войти в режим!')

async def get_recent_coordinats(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        user_id = message.from_user.id
        cursor = await db.execute('SELECT latitude_db, longitude_db, time_db, cities_db FROM users WHERE user_id = ? ORDER BY id DESC LIMIT 5', (user_id,))
        results = await cursor.fetchall()

        if results:
            text = ''
            for lat, lon, time, city in results:
                normal_time_text = (f'Время: {time[11:13]}:{time[14:16]} \n'
                                    f'День: {time[8:10]}-{time[5:7]}-{time[:4]}\n\n')
                text_coordinats = f'Широта: {lat} Долгота: {lon}\n'
                text_cities = f'Город: {city}\n'
                text += text_coordinats + text_cities + normal_time_text
            await message.answer(f'{text}\n Чтобы очистить историю, напишите /clear')

        else:
            await message.answer('Вы еще не отправляли геопозицию')

async def cmd_clear(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        user_id = message.from_user.id
        cursor = await db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        await db.commit()
    await message.answer('История очищена!')

router.message.register(cmd_start, Command(commands='start'))
router.message.register(cmd_clear, Command(commands='clear'))
router.message.register(check_coordinats, F.location)
router.message.register(get_recent_coordinats, F.text == 'Мои последние геопозиции.')
router.message.register(input_city, F.text=='Погода в введеном городе.')
router.message.register(send_input_city, F.text)
