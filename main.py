from aiogram.types import BotCommandScopeAllPrivateChats
import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from database.engine import create_db, drop_db, session_maker
from handlers.callbacks import callback_router
from handlers.user_group import user_group_router
from handlers.user_private import user_private_router
from handlers.admin_private import admin_router
from middlewares.db import DataBaseSession
from common.bot_cmd_list import private


async def on_startup():
    run_param = False
    if run_param:
        await drop_db()
    await create_db()


async def on_shutdown():
    print('бот лег')


bot = Bot(token=os.getenv('TOKEN'), parse_mode=ParseMode.HTML)
dp = Dispatcher()
dp.include_routers(user_private_router, user_group_router, admin_router, callback_router)
dp.update.middleware(DataBaseSession(session_pool=session_maker))
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)
bot.my_admins_list = [int(i) for i in os.getenv('ADMIN').split(' ')]


async def main():
    # await bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    # await bot.set_my_commands(commands=private, scope=BotCommandScopeAllPrivateChats())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
