from aiogram import Bot, Dispatcher

from core.config import Config

token = Config('telegram_token', cfg_type=str)

if token:
    bot = Bot(token=token)
    dp = Dispatcher()
else:
    bot = dp = False
