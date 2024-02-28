from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_delete_product, orm_get_product
from handlers.admin_private import AddProduct

callback_router = Router()


@callback_router.callback_query(F.data.startswith("delete_"))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))
    await callback.answer("Товар удален", show_alert=True)  # нужен для подтверждения нажатия кнопки
    await callback.message.answer("Товар удален!")


@callback_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    AddProduct.product_for_change = await orm_get_product(session, int(product_id))
    await callback.answer()
    await callback.message.answer("Введите название товара", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddProduct.name)
