import asyncio

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from db.models import Artist, Person
from app import bot
from app.filters.callbacks import order_data, artist_callback


async def user_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    Person.get_or_create(
        id=message.from_user.id,
        defaults=dict(
            name=message.from_user.username,
            real_name=message.from_user.full_name
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            'Показать всех художников',
            callback_data=artist_callback.new(0, 'switch') 
        ),
        types.InlineKeyboardButton(
            'Ваши заказы', callback_data='client_orders'
        )
    )
    await message.answer(
        'Привет! Этот бот поможет тебе общаться с художниками '
        'и купить у них работу.',
        reply_markup=keyboard
    )


async def show_artist(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    count_artist = Artist.select().count()
    if count_artist == 0:
        return await call.message.edit_text(
            'Здесь пока нет художников('
        )
    artists = list(Artist.select().order_by(Artist.id))
    index_artist = int(callback_data['index'])
    index_artist = (index_artist % count_artist) if index_artist != 0 else 0
    artist: Artist = artists[index_artist]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            '<',
            callback_data=artist_callback.new(index_artist - 1, action='switch')
        ),
        types.InlineKeyboardButton(
            '>',
            callback_data=artist_callback.new(index_artist + 1, action='switch')
        ),
        types.InlineKeyboardButton(
            'Сделать заказ у художника',
            callback_data=order_data.new(order_id=artist.id, action='new_order')
        ),
    )
    await call.answer('Переключаю ...')

    data = await state.get_data()
    photo_messages: list[types.Message] = data.get('photo_messages', [])
    await state.reset_data()
    await asyncio.gather(
        *[bot.delete_message(call.from_user.id, message.message_id)
        for message in photo_messages]
    )
    await call.message.delete()
    await call.message.answer(
        f'Художник #{index_artist};\n'
        f'Имя: {artist.person.real_name}\n'
        f'Описания: {artist.description}',
        reply_markup=keyboard
    )
    if artist.photos:
        photo_messages = await call.message.answer_media_group(
            [types.InputMediaPhoto(photo.file_id) for photo in artist.photos]
        )
        await state.update_data({'photo_messages': photo_messages})



def register_user_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_artist, artist_callback.filter(action='switch')
    )
