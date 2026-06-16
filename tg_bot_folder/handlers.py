from aiogram.filters.command import Command
from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
WEATHER_KEY = 'https://api.open-meteo.com/v1/forecast'
WEATHER_KEY2 = 'https://geocoding-api.open-meteo.com/v1/search'
DB_NAME = 'recent_cities.sql'
url_nomination = 'https://nominatim.openstreetmap.org/reverse'
import tg_bot_folder.keybord as keybord

import aiohttp
import aiosqlite
import datetime

weather_dictionary = {
    (0,1,2): '☀️ Ясно',
    (3,): '☁️ Пасмурно',
    (45,51,53,55): '🌫️ Туман',
    (61,63): '🌧️ Слабый дождь',
    (65,): '🌧️ Сильный дождь',
    (71,73): '🌨️ Слабый снег',
    (75,): '🌨️ Сильный снег',
    (80,81,82): 'Ливень',
    (95,): '⛈️ Гроза',
    (96,99): '⛈️ Гроза с градом',
}

router = Router()
in_input_city = False

class FutureDaysStates(StatesGroup):
    waiting_geoposition = State()
    waiting_date = State()

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
                return 'api error: {response.status}'


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
        my_params = {'latitude': my_latitude, 'longitude': my_longitude, 'timezone': 'auto', 'hourly': 'temperature_2m,weather_code'}

        async with session.get(WEATHER_KEY, params=my_params) as response:
            if response.status == 200:
                my_data = await response.json()
                my_code_weather = my_data['hourly']['weather_code'][0]
                current_temp = my_data['hourly']['temperature_2m'][0]

                for codes, states in weather_dictionary.items():
                    if my_code_weather in codes:
                        state = states
                        break
                    else:
                        state = 'Нет состояния'

                await message.answer(f'Температура сейчас: {current_temp}°C \n' 
                                     f'На координаты: {my_latitude}, {my_longitude}\n'
                                     f'Состояние: {state}\n'
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
                                 'hourly': 'temperature_2m,weather_code'}

                    async with aiosqlite.connect(DB_NAME) as db:
                        await db.execute('INSERT INTO users(user_id, latitude_db, longitude_db, time_db, cities_db) VALUES(?,?,?,?,?)', (id_user, first_element['latitude'], first_element['longitude'], time, first_element['name']))
                        await db.commit()

                    async with session.get(WEATHER_KEY, params=my_params) as response:
                        if response.status == 200:
                            my_data2 = await response.json()
                            current_temp = my_data2['hourly']['temperature_2m'][0]
                            my_code_weather = my_data2['hourly']['weather_code'][0]

                            for codes, states in weather_dictionary.items():
                                if my_code_weather in codes:
                                    state = states
                                    break
                                else:
                                    state = 'Нет состояния'

                            await message.answer(f'Температура сейчас: {current_temp}°C \n'
                                                 f'На координаты: {first_element['latitude']}, {first_element['longitude']}\n'
                                                 f'Состояние: {state}\n'
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

            await message.answer(f'{text}\n /clear - очистка истории.')

        else:
            await message.answer('Вы еще не отправляли геопозицию')

async def cmd_clear(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        user_id = message.from_user.id
        await db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        await db.commit()
    await message.answer('История очищена!')

async def future_days_menu(message: types.Message):
    await message.answer('Выберите количество дней.', reply_markup=keybord.choice_days_buttons)

async def return_to_main(message: types.Message):
    await message.answer('Возращаемся в главное меню.', reply_markup=keybord.main)

async def on_3days(message: types.Message, state: FSMContext):
    await state.set_state(FutureDaysStates.waiting_geoposition)
    await state.update_data(days=3)
    await message.answer('Введите название города или сбросьте геопозицию.')

async def on_7days(message: types.Message, state: FSMContext):
    await state.set_state(FutureDaysStates.waiting_geoposition)
    await state.update_data(days=7)
    await message.answer('Введите название города или сбросьте геопозицию.')

async def create_calendar(message: types.Message, state: FSMContext):
    await state.set_state(FutureDaysStates.waiting_date)
    today = datetime.datetime.now().date()

    calendar = SimpleCalendar(locale='ru_RU')
    await message.answer('Выберите дату:\n'
                         '(Максимум 16 дней, минимум сегодняшний день).',
                         reply_markup=await calendar.start_calendar())

async def on_special_day(callback: types.CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar(locale='ru_RU')
    selected, selected_date = await calendar.process_selection(callback, callback_data)

    if selected:
        today = datetime.datetime.now().date()
        max_day = today + datetime.timedelta(days=15)

        if selected_date.date() < today or selected_date.date() > max_day:
            await callback.message.delete()
            await callback.message.answer('Можно выбрать только текущую дату и на 16 дней вперед.')
        else:
            text = selected_date.strftime('%Y-%m-%d')
            await state.set_state(FutureDaysStates.waiting_geoposition)
            await state.update_data(days=text)
            await callback.message.delete()
            await callback.message.answer(f'Введите город или сбросьте геопозицию, чтобы узнать погоду на {text}')


async def reg_on_geo(message: types.Message, state: FSMContext):

    my_latitude = message.location.latitude
    my_longitude = message.location.longitude
    city = await city_by_coordinats(message)
    state_data = await state.get_data()
    days = state_data.get('days')
    async with aiohttp.ClientSession() as session:
        if str(days).isdigit():
            my_params = {'latitude': my_latitude, 'longitude': my_longitude, 'timezone': 'auto',
                         'hourly': 'temperature_2m,weather_code', 'forecast_days': days}
        else:
            my_params = {'latitude': my_latitude, 'longitude': my_longitude, 'timezone': 'auto', 'hourly': 'temperature_2m', 'start_date': days, 'end_date': days}
        async with session.get(WEATHER_KEY, params=my_params) as response:
            if response.status == 200:
                my_data = await response.json()
                times = my_data['hourly']['time']
                temperatures = my_data['hourly']['temperature_2m']
                text = ''
                count_day = 0
                for i in range(0, len(times), 24):
                    count_day += 1
                    text += (f'{count_day}# Дата: {times[i][8:10]}-{times[i][5:7]}-{times[i][:4]}\n'
                            f'Температура: {temperatures[i]}°C\n'
                            f'В городе: {city}\n\n')
                await message.answer(text)
            else:
                await message.answer("Ошибка апи")
    await state.clear()

async def reg_on_text(message: types.Message, state: FSMContext):

    state_data = await state.get_data()
    days = state_data.get('days')
    async with aiohttp.ClientSession() as session:
        city = message.text
        my_params = {'name': city, 'language': 'ru', 'format': 'json'}
        async with session.get(WEATHER_KEY2, params=my_params) as response:
            if response.status == 200:
                my_data = await response.json()
                first_element = my_data['results'][0]
                if str(days).isdigit():
                    my_params2 = {'latitude': first_element['latitude'], 'longitude': first_element['longitude'],'timezone': 'auto','hourly': 'temperature_2m', 'forecast_days':days}
                else:
                    my_params2 = {'latitude': first_element['latitude'], 'longitude': first_element['longitude'], 'timezone': 'auto',
                                 'hourly': 'temperature_2m', 'start_date': days, 'end_date': days}

                async with session.get(WEATHER_KEY, params=my_params2) as response:
                    if response.status == 200:
                        my_data = await response.json()

                        times = my_data['hourly']['time']
                        temperatures = my_data['hourly']['temperature_2m']
                        text = ''
                        count_day = 0
                        for i in range(0, len(times), 24):
                            count_day += 1
                            text += (f'{count_day}# Дата: {times[i][8:10]}-{times[i][5:7]}-{times[i][:4]}\n'
                                     f'Температура: {temperatures[i]}°C\n'
                                     f'В городе: {city}\n\n')
                        await message.answer(text)
                    else:
                        await message.answer("Ошибка апи")
    await state.clear()

router.message.register(cmd_start, Command(commands='start'))
router.message.register(cmd_clear, Command(commands='clear'))


router.message.register(future_days_menu, F.text == 'Прогноз на будущие дни.')
router.message.register(return_to_main, F.text == 'Назад.')

router.message.register(on_3days, F.text == 'На 3 дня.')
router.message.register(on_7days, F.text == 'На неделю.')
router.message.register(create_calendar, F.text == 'На определенную дату.')
router.callback_query.register(on_special_day, SimpleCalendarCallback.filter())

router.message.register(reg_on_geo, F.location, FutureDaysStates.waiting_geoposition)
router.message.register(reg_on_text, F.text, FutureDaysStates.waiting_geoposition)

router.message.register(check_coordinats, F.location)
router.message.register(get_recent_coordinats, F.text == 'Мои последние геопозиции.')
router.message.register(input_city, F.text=='Погода в введеном городе.')
router.message.register(send_input_city, F.text)
