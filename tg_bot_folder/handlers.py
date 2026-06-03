from aiogram.filters.command import Command
from aiogram import Router, types, F
WEATHER_KEY = 'https://api.open-meteo.com/v1/forecast'
WEATHER_KEY2 = 'https://geocoding-api.open-meteo.com/v1/search'
url_nomination = 'https://nominatim.openstreetmap.org/reverse'
import tg_bot_folder.keybord as keybord

import aiohttp

router = Router()
in_input_city = False

async def cmd_start(message: types.Message):
    await message.answer(f"Привет {message.from_user.first_name}! Я бот о погоде. Отправь мне свой город и я покажу погоду.", reply_markup=keybord.main)


async def city_by_coordinats(message: types.Message):
    params_nomination = {'format': 'json', 'lat': message.location.latitude, 'lon': message.location.longitude, 'accept-language': 'ru-RU', 'email': 'pvzrus2@gmail.com'}
    async with aiohttp.ClientSession(headers={'User-Agent': 'MyWeatherBot/1.0 pvzrus2@gmail.com'}) as session:
        async with session.get(url_nomination, params=params_nomination) as response:
            city = None
            if response.status == 200:
                data_nomination = await response.json()
                city = data_nomination.get('display_name', '')
                return ','.join(city)
            else:
                print(f'api error: {response.status}')



async def check_coordinats(message: types.Message):
    my_latitude = message.location.latitude
    my_longitude = message.location.longitude

    city = await city_by_coordinats(message)

    async with aiohttp.ClientSession() as session:
        my_params = {'latitude': my_latitude, 'longitude': my_longitude, 'timezone': 'auto', 'hourly': 'temperature_2m'}

        async with session.get(WEATHER_KEY, params=my_params) as response:
            if response.status == 200:
                my_data = await response.json()
                current_temp = my_data['hourly']['temperature_2m'][0]

                await message.answer(f'Температура сейчас: {current_temp}°C \n' 
                                     f'На координаты: {my_latitude}, {my_longitude}\n'
                                     f'В городе: {await city_by_coordinats(message)}')
            else:
                await message.answer('Что то не так')


async def input_city(message: types.Message):
    global in_input_city
    in_input_city = True
    await message.answer('Введи любой город!')

async def send_input_city(message: types.Message):
    if in_input_city:
        async with aiohttp.ClientSession() as session:
            city_user = message.text
            my_params = {'name': city_user, 'language': 'ru', 'format': 'json'}
            async with session.get(WEATHER_KEY, params=my_params) as response:
                if response.status == 200:
                    my_data = await response.json()
                    await message.answer(my_data)
                    print(my_data)
                else:
                    await message.answer('Что то не так')
    else:
        await message.answer('Сначала нужно войти в режим!')

router.message.register(cmd_start, Command(commands='start'))
router.message.register(check_coordinats, F.location)
router.message.register(input_city, F.text=='Погода в введеном городе.')
router.message.register(send_input_city, F.text)