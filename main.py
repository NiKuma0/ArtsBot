import logging

from aiogram import Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from app import bot
from db.models import create_tables
from app.handlers import __all__ as handlers
from app.middlewares import AlbumMiddleware, UserUpdate


logger_file_handler = logging.FileHandler('bot.log')
logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setLevel(logging.INFO)
logger_stream_handler.setFormatter(logging.Formatter(
    '[%(levelname)s %(asctime)s]\n%(message)s', datefmt='"%d/%m %H.%M"',
))
logger_file_handler.setLevel(logging.DEBUG)
logging.basicConfig(
    datefmt='"%d/%m %H.%M"',
    format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
    level=logging.DEBUG,
    handlers=(logger_file_handler, logger_stream_handler)
)

def main():
    dp = Dispatcher(bot, storage=MemoryStorage())
    dp.middleware.setup(AlbumMiddleware())
    dp.middleware.setup(LoggingMiddleware())
    dp.middleware.setup(UserUpdate())
    create_tables()
    [func(dp) for func in handlers]
    executor.start_polling(dp)


if __name__ == '__main__':
    main()
