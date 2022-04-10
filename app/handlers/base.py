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
        await data.message.answer(text)
        await data.message.delete()
    if isinstance(data, types.Message):
        await data.answer(text)


async def reg_user(message: types.Message):
    user = message.from_user
    _, created = Person.get_or_create(
        id=user.id,
        defaults=dict(
            name=user.username,
            real_name=user.full_name
        )
    )
    if not created:
        return await message.answer('Вы уже в бд!')
    
    await message.answer('Теперь вы в бд!')


def register_base_handler(dp: Dispatcher):
    dp.register_message_handler(main_start, commands=('start',))
    dp.register_message_handler(cancel, commands='cancel')
    dp.register_callback_query_handler(cancel, lambda call: call.data == 'cancel')
    dp.register_message_handler(reg_user, commands='reg_user')
