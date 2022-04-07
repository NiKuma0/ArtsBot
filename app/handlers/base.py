import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from db.models import Artist, Person
from app import bot
from .user import user_start
from .artist import artist_start


logger = logging.getLogger(__name__)


async def main_start(message: types.Message, state: FSMContext):
    await state.finish()
    name = message.from_user.username
    if Artist.select().join(Person).where(Person.name == name).exists():
        return await artist_start(message)
    await user_start(message)


async def cancel(data: types.Message | types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = 'Отменено! Чтобы открать меню, нажмите /start'
    if isinstance(data, types.CallbackQuery):
        await data.message.edit_text(text)
    if isinstance(data, types.Message):
        await data.answer(text)


async def reg_user(message: types.Message, state: FSMContext):
    user = message.from_user
    _, created = Person.get_or_create(
        id=user.id,
        name=user.username,
        real_name=user.full_name
    )
    if created:
        return await message.answer('Теперь вы в бд!')
    await message.answer('Вы уже в бд!')


def register_base_handler(dp: Dispatcher):
    dp.register_message_handler(main_start, commands=('start',))
    dp.register_message_handler(cancel, commands='cancel')
    dp.register_callback_query_handler(cancel, lambda call: call.data == 'cancel')
    dp.register_message_handler(reg_user, commands='reg_user')
