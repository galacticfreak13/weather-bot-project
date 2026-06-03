from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard = [[KeyboardButton(text='Погода в моем местоположении.', request_location=True)],
                                      [KeyboardButton(text = 'Погода в введеном городе.')]],
                           input_field_placeholder='Узнаем погоду...')

