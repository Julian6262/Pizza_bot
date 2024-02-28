from string import punctuation
from aiogram import types, Router
from filters.chat_types import ChatTypeFilter

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))
# user_group_router.edited_message.filter(ChatTypeFilter(["group", "supergroup"]))

restricted_words = {'кабан', 'хомяк', 'лось'}


# удалить знаки в словах, если пытаются скрыть мат
def clean_text(text: str):
    return text.translate(str.maketrans('', '', punctuation))


@user_group_router.message()
@user_group_router.edited_message()  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
async def message_with_cleaner(message: types.Message):
    if restricted_words.intersection(clean_text(message.text.lower()).split()):
        await message.answer(f'{message.from_user.first_name}, соблюдайте порядок в чате, не ругайтесь!')
        await message.delete()
