from aiogram import types, Dispatcher
from aiogram.utils.callback_data import CallbackData

from db.models import Artist, Person
from app import bot
from .orders import order_data


artist_callback = CallbackData('artist', 'index', 'action')


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


async def show_artist(call: types.CallbackQuery, callback_data: dict):
    count_artist = Artist.select().count()
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
            callback_data=order_data.new(id=artist.id, action='new_order')
        ),
    )
    await call.answer('Переключаю ...')
    await call.message.edit_text(
        f'Художник #{index_artist};\n'
        f'Имя: {artist.person.real_name}\n'
        f'Описания: {artist.description}',
        reply_markup=keyboard
    )


def register_user_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_artist, artist_callback.filter(action='switch')
    )
