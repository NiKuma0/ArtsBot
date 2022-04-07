from aiogram import types, Dispatcher
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


from db.models import Artist, Message, Person
from app import bot

artist_callback = CallbackData('artist', 'index', 'action')


class Messaging(StatesGroup):
    start_messaging = State()


async def user_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            'Показать всех художников',
            callback_data=artist_callback.new(0, 'switch') 
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
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            '<',
            callback_data=artist_callback.new(index_artist - 1, action='switch')
        ),
        types.InlineKeyboardButton(
            'Написать',
            callback_data=artist_callback.new(index_artist, action='message')
        ),
        types.InlineKeyboardButton(
            '>',
            callback_data=artist_callback.new(index_artist + 1, action='switch')
        )
    )
    await call.answer('Переключаю ...')
    await call.message.edit_text(
        f'Художник #{index_artist};\n'
        f'Имя: {artist.person.real_name}\n'
        f'Описания: {artist.description}',
        reply_markup=keyboard
    )


async def start_messaging(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await Messaging.start_messaging.set()
    artists = list(Artist.select().order_by(Artist.id))
    index_artist = int(callback_data['index'])
    artist: Artist = artists[index_artist]
    await state.update_data({'artist_id': artist.id})
    await call.message.edit_text('Что хотите ему написать? (чтобы остановить нажмите /cancel)')


async def send_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    artist: Artist = Artist.get_by_id(data['artist_id'])
    user, _ = Person.get_or_create(
        id=message.from_user.id,
        name=message.from_user.username,
        real_name=message.from_user.full_name
    )
    Message.create(
        text=message.text,
        user=user.id,
        artist=artist,
        date=message.date,
    )
    await bot.send_message(artist.person.id, 'У вас новое сообщение!')
    await message.answer('Сообщение отправлено! (чтобы остановить нажмите /cancel)')


def register_user_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_artist, artist_callback.filter(action='switch')
    )
    dp.register_callback_query_handler(
        start_messaging, artist_callback.filter(action='message')
    )
    dp.register_message_handler(
        send_message, state=Messaging.start_messaging
    )
