from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

start_keyboard = ReplyKeyboardBuilder()
start_keyboard.add(KeyboardButton(text='Меню'),
                   KeyboardButton(text='О магазине 😀'),
                   KeyboardButton(text='Варианты оплаты'),
                   KeyboardButton(text='Варианты доставки'),
                   )
start_keyboard.adjust(2, 1, 1)
start_keyboard = start_keyboard.as_markup(resize_keyboard=True, )

admin_keyboard = ReplyKeyboardBuilder()
admin_keyboard.add(KeyboardButton(text='Добавить товар'),
                   KeyboardButton(text='Ассортимент'),
                   )
admin_keyboard.adjust(2, )
admin_keyboard = admin_keyboard.as_markup(resize_keyboard=True, input_field_placeholder='Выберите действие')
