import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from db.models import Artist, Person
from app import bot


logger = logging.getLogger(__name__)


class SetProfile(StatesGroup):
    name = State()
    description = State()
    wait_done = State()


class MessageAnswer(StatesGroup):
    answer = State()


async def artist_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(
            'Ваши заказы', callback_data='artist_orders'
        ),
        types.InlineKeyboardButton(
            'Перезаполнить профиль', callback_data='profile'
        ),
    )
    person: Person = Person.get_by_id(message.from_user.id)
    await message.answer(
        'Привет! Твой профиль:\n'
        f'Имя: {person.real_name}\n'
        f'Описания: {person.artist.first().description}\n',
        reply_markup=keyboard
    )


async def profile(call: types.CallbackQuery, state: FSMContext):
    await SetProfile.name.set()
    await state.update_data({'artist_id': call.from_user.id})
    await call.message.edit_text('Заполните информацию (чтобы отменить изменения нажмите /cancel)')
    await call.message.answer('Напишите мне ваше имя:')


async def set_name(message: types.Message, state: FSMContext):
    await SetProfile.description.set()
    await state.update_data({'artist_name': message.text})
    await message.answer('Напишите мне описания своего профиля:')


async def set_description(message: types.Message, state: FSMContext):
    await SetProfile.wait_done.set()
    await state.update_data({'artist_description': message.text})
    data = await state.get_data()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            'Готово!', callback_data='save_profile',
        ),
        types.InlineKeyboardButton(
            'Отмена', callback_data='cancel',
        ),
    )
    await message.answer(
        'Подвердите профиль:\n'
        f'Имя: {data["artist_name"]}\n'
        f'Описания: {data["artist_description"]}\n',
        reply_markup=keyboard
    )


async def save_profile(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    person: Person = Person.get_by_id(data['artist_id'])
    artist: Artist = person.artist.first()
    person.real_name = data['artist_name']
    artist.description = data['artist_description']
    artist.save()
    person.save()
    await call.message.edit_text('Профиль изменён! Чтобы открать меню нажмите /start')


def register_artist_handler(dp: Dispatcher):
    dp.register_callback_query_handler(profile, lambda c: c.data == 'profile')
    dp.register_message_handler(set_name, state=SetProfile.name)
    dp.register_message_handler(set_description, state=SetProfile.description)
    dp.register_callback_query_handler(
        save_profile,
        lambda c: c.data == 'save_profile',
        state=SetProfile.wait_done
    )
