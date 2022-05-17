import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from db.models import Artist, Person, Photo
from app.filters.states import SetProfile
from app import bot


logger = logging.getLogger(__name__)


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
    artist = Person.get_by_id(call.from_user.id).artist.first()
    await state.update_data({'artist': artist})
    await call.message.edit_text('Заполните информацию (чтобы отменить нажмите /cancel)')
    await call.message.answer('Напишите мне ваше имя:')


async def set_name(message: types.Message, state: FSMContext):
    await SetProfile.description.set()
    artsit: Artist = (await state.get_data())['artist']
    artsit.person.name = message.text
    await state.update_data({'artist': artsit})
    await message.answer('Напишите мне описания своего профиля:')


async def set_description(message: types.Message, state: FSMContext):
    await SetProfile.photos.set()
    artist: Artist = (await state.get_data())['artist']
    artist.description = message.text
    await state.update_data({'artist': artist})
    await message.answer('Теперь пришли мне фото примеров работ')


async def set_photos(message: types.Message, state: FSMContext, album: list[types.Message]=[]):
    data = await state.get_data()
    await SetProfile.wait_done.set()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            'Готово!', callback_data='save_profile',
        ),
        types.InlineKeyboardButton(
            'Отмена', callback_data='cancel',
        ),
    )

    photos = [
        album_message.photo[-1]
        for album_message in album
    ]
    if not album:
        photos = [message.photo[-1]]
    artist = (await state.get_data())['artist']
    artist.photos.add(
        Photo.create_album(photos),
        clear_existing=True
    )
    await state.update_data({'artist': artist})

    await message.answer_media_group(
        media=types.MediaGroup(
            [types.InputMediaPhoto(photo) for photo in photos]
        ),
    )
    await message.answer(
        text='Подвердите профиль:\n'
        f'Имя: {data["artist_name"]}\n'
        f'Описания: {data["artist_description"]}\n',
        reply_markup=keyboard
    )


async def save_profile(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    artist = data['artist']
    artist.save()
    artist.person.save()
    await call.message.edit_text('Профиль изменён! Чтобы открать меню нажмите /start')


def register_artist_handler(dp: Dispatcher):
    dp.register_callback_query_handler(profile, lambda c: c.data == 'profile')
    dp.register_message_handler(set_name, state=SetProfile.name)
    dp.register_message_handler(set_description, state=SetProfile.description)
    dp.register_message_handler(
        set_photos,
        content_types='photo',
        state=SetProfile.photos,
    )
    dp.register_callback_query_handler(
        save_profile,
        lambda c: c.data == 'save_profile',
        state=SetProfile.wait_done
    )
