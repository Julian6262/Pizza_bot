from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_product, orm_update_product, orm_get_categories, orm_delete_product, \
    orm_get_product, orm_get_info_pages, orm_change_banner_image, orm_get_products
from filters.chat_types import ChatTypeFilter, IsAdmin
from keyboards.keyboards import get_reply_keyboard, get_inline_keyboard

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


class AddBanner(StatesGroup):
    image = State()


class AddProduct(StatesGroup):
    name = State()
    description = State()
    category = State()
    price = State()
    image = State()
    product_for_change = None


admin_kb = get_reply_keyboard(
    "Добавить товар",
    "Ассортимент",
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)


@admin_router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=admin_kb)


@admin_router.message(F.text == 'Ассортимент')
async def admin_features(message: types.Message, session: AsyncSession):
    categories = await orm_get_categories(session)
    btns = {category.name: f'category_{category.id}' for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_inline_keyboard(btns=btns))


@admin_router.callback_query(F.data.startswith('category_'))
async def starring_at_product(callback: types.CallbackQuery, session: AsyncSession):
    category_id = callback.data.split('_')[-1]
    for product in await orm_get_products(session, int(category_id)):
        await callback.message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}</strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_inline_keyboard(btns={
                "Удалить": f"delete_{product.id}",
                "Изменить": f"change_{product.id}",
            },
                sizes=(2,)
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список товаров ⏫")


# ⏩⏩⏩ FSM для добавления/изменения товаров админом ⏪⏪⏪ ########################################################
@admin_router.callback_query(StateFilter(None), F.data.startswith("delete_"))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))
    await callback.answer("Товар удален", show_alert=True)  # нужен для подтверждения нажатия кнопки
    await callback.message.answer("Товар удален!")


@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    AddProduct.product_for_change = await orm_get_product(session, int(product_id))
    await callback.answer()
    await callback.message.answer("Введите название товара", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddProduct.name)


# Становимся в состояние ожидания ввода name
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddProduct.name)


# Хендлер отмены и сброса состояния
@admin_router.message(StateFilter(AddProduct, AddBanner), Command("отмена"))
@admin_router.message(StateFilter(AddProduct, AddBanner), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    AddProduct.product_for_change = None
    await message.answer("Действия отменены", reply_markup=admin_kb)


# Вернутся на шаг назад (на прошлое состояние)
@admin_router.message(StateFilter(AddProduct, AddBanner), Command("назад"))
@admin_router.message(StateFilter(AddProduct, AddBanner), F.text.casefold() == "назад")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == AddProduct.name or current_state == AddBanner.image:
        await state.clear()
        AddProduct.product_for_change = None
        await message.answer("Возврат в меню", reply_markup=admin_kb)
    else:
        previous_state = AddProduct.__all_states__[AddProduct.__all_states__.index(current_state) - 1]
        await state.set_state(previous_state.state)
        await message.answer(f"Вы вернулись к прошлому шагу {previous_state.state}")


@admin_router.message(AddProduct.name)
async def add_name(message: types.Message, state: FSMContext):
    if message.text and message.text != ".":
        if len(message.text) >= 150:
            await message.answer("Название товара не должно превышать 150 символов. \n Введите заново")
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
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text != ".":
        await state.update_data(description=message.text)
    elif message.text == "." and AddProduct.product_for_change:
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        await message.answer("Веден неправильный формат, повторите ввод")
        return

    categories = await orm_get_categories(session)
    btns = {category.name: str(category.id) for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_inline_keyboard(btns=btns))
    await state.set_state(AddProduct.category)


@admin_router.callback_query(AddProduct.category)
async def category_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.update_data(category=callback.data)
    await callback.answer()
    await callback.message.answer('Теперь введите цену товара.')
    await state.set_state(AddProduct.price)


# Ловим любые некорректные действия, кроме нажатия на кнопку выбора категории(колбэк выше)
@admin_router.message(AddProduct.category)
async def category_choice2(message: types.Message):
    await message.answer('Выберите категорию из кнопок.')


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
        await message.answer("Товар добавлен/изменен", reply_markup=admin_kb)
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру, он опять денег хочет", reply_markup=admin_kb)

    await state.clear()
    AddProduct.product_for_change = None


# ⏩⏩⏩ Микро FSM для загрузки/изменения баннеров ⏪⏪⏪ ###########################################################
# Отправляем перечень информационных страниц бота и становимся в состояние отправки photo
@admin_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\n{', '.join(pages_names)}")
    await state.set_state(AddBanner.image)


# Добавляем/изменяем изображение в таблице (там уже есть записанные страницы по именам)
@admin_router.message(AddBanner.image)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.photo:
        image_id = message.photo[-1].file_id
        for_page = message.caption.strip()
        pages_names = [page.name for page in await orm_get_info_pages(session)]
        if for_page not in pages_names:
            await message.answer(f"Введите нормальное название страницы, например:\n{', '.join(pages_names)}")
            return
        await orm_change_banner_image(session, for_page, image_id, )
        await message.answer("Баннер добавлен/изменен.")
        await state.clear()
    else:
        await message.answer("Веден неправильный формат, повторите ввод")
        return
