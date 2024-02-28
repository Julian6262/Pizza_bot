from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_product, orm_get_products, orm_update_product
from filters.chat_types import ChatTypeFilter, IsAdmin
from keyboards.inline import get_inline_btns
from keyboards.reply import admin_keyboard

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    image = State()
    product_for_change = None


@admin_router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=admin_keyboard)


@admin_router.message(F.text == "Ассортимент")
async def show_product(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}</strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_inline_btns(btns={
                'Удалить товар': f'delete_{product.id}',
                'Изменить товар': f'change_{product.id}'
            })
        )
    await message.answer("ОК, вот список товаров ⬆️")


# Код ниже для машины состояний (FSM)
# Становимся в состояние ожидания ввода name
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddProduct.name)


# Хендлер отмены и сброса состояния должен быть всегда именно здесь,
# после того как только встали в состояние номер 1 (элементарная очередность фильтров)
@admin_router.message(StateFilter(AddProduct), Command("отмена"))
@admin_router.message(StateFilter(AddProduct), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    AddProduct.product_for_change = None
    await message.answer("Действия отменены", reply_markup=admin_keyboard)


# Вернутся на шаг назад (на прошлое состояние)
@admin_router.message(StateFilter(AddProduct), Command("назад"))
@admin_router.message(StateFilter(AddProduct), F.text.casefold() == "назад")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == AddProduct.name:
        await state.clear()
        AddProduct.product_for_change = None
        await message.answer("Возврат в меню", reply_markup=admin_keyboard)
    else:
        previous_state = AddProduct.__all_states__[AddProduct.__all_states__.index(current_state) - 1]
        await state.set_state(previous_state.state)
        await message.answer(f"Вы вернулись к прошлому шагу {previous_state.state}")


@admin_router.message(AddProduct.name)
async def add_name(message: types.Message, state: FSMContext):
    if message.text and message.text != ".":
        if len(message.text) >= 100:
            await message.answer("Название товара не должно превышать 100 символов. \n Введите заново")
            return
        await state.update_data(name=message.text)
    elif message.text == "." and AddProduct.product_for_change:  # Если введена точка, то пропускаем изменение
        await state.update_data(name=AddProduct.product_for_change.name)
    else:
        await message.answer("Веден неправильный формат, повторите ввод")
        return

    await message.answer("Введите описание товара")
    await state.set_state(AddProduct.description)


# Ловим данные для состояния description и потом меняем состояние на price
@admin_router.message(AddProduct.description)
async def add_description(message: types.Message, state: FSMContext):
    if message.text and message.text != ".":
        await state.update_data(description=message.text)
    elif message.text == "." and AddProduct.product_for_change:
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        await message.answer("Веден неправильный формат, повторите ввод")
        return

    await message.answer("Введите стоимость товара")
    await state.set_state(AddProduct.price)


@admin_router.message(AddProduct.price)
async def add_price(message: types.Message, state: FSMContext):
    if message.text and message.text != ".":
        try:
            await state.update_data(price=float(message.text))
        except (ValueError, TypeError):
            await message.answer("Введите корректное значение цены")
            return
    elif message.text == "." and AddProduct.product_for_change:
        await state.update_data(price=AddProduct.product_for_change.price)
    else:
        await message.answer("Веден неправильный формат, повторите ввод")
        return

    await message.answer("Загрузите изображение товара")
    await state.set_state(AddProduct.image)


@admin_router.message(AddProduct.image)
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.photo:
        await state.update_data(image=message.photo[-1].file_id)
    elif message.text == "." and AddProduct.product_for_change:
        await state.update_data(image=AddProduct.product_for_change.image)
    else:
        await message.answer("Веден неправильный формат, повторите ввод")
        return

    try:
        data = await state.get_data()
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар добавлен/изменен", reply_markup=admin_keyboard)
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру, он опять денег хочет", reply_markup=admin_keyboard)

    await state.clear()
    AddProduct.product_for_change = None
