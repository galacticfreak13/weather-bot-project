from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard = [[KeyboardButton(text='Погода в моем местоположении.', request_location=True)],
                                      [KeyboardButton(text = 'Погода в введеном городе.')],
                                       [KeyboardButton(text = 'Мои последние геопозиции.')],
                                       [KeyboardButton(text = 'Прогноз на будущие дни.')]],
                           input_field_placeholder='Узнаем погоду...')
choice_days_buttons = ReplyKeyboardMarkup(keyboard=
                                          [[KeyboardButton(text='На 3 дня.')],
                                          [KeyboardButton(text='На неделю.')],
                                           [KeyboardButton(text='На определенную дату.')],
                                           [KeyboardButton(text='Назад.')]])
