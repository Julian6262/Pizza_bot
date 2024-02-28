from aiogram import types, Router, F
from aiogram.filters import Command, or_f
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_products
from keyboards.reply import start_keyboard
from menu.menu import text
from filters.chat_types import ChatTypeFilter

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))


@user_private_router.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer('Привет, я виртуальный помощник', reply_markup=start_keyboard)


@user_private_router.message(or_f(Command('menu'), F.text.lower() == 'меню'))
async def cmd_menu(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}</strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
        )
    await message.answer('Вот меню ⬆️')


@user_private_router.message(F.text.lower() == 'варианты доставки')
async def variant(message: types.Message):
    await message.answer(text.as_html())
