from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.utils.callback_data import CallbackData, CallbackDataFilter

from db.models import Person, Order, Artist, Comment
from .comments import comment_data
from app import bot
from app.tools import notify
from config import ADMINS_NAME


class StateOrder(StatesGroup):
    wait_description = State()
    wait_status = State()
    change_or_create = State()


class TextOrderFilter(Text):
    async def check(self, obj: types.Message):
        result = await super().check(obj)
        if not result:
            return result
        order = await self.get_order(obj)
        role = await self.has_perm(obj, order)
        return {'order': order, 'role': role}
    
    async def get_order(self, message: types.Message) -> Order:
        order_id = message.text.removeprefix(self.startswith[0])
        try:
            order: Order = Order.get_by_id(order_id)
        except Order.DoesNotExist:
            await message.answer('Заказ не найден!')
            raise CancelHandler()
        return order
    
    async def has_perm(self, message: types.Message, order: Order) -> str:
        user = message.from_user
        if user.username in ADMINS_NAME:
            return 'admin'
        if user.id == order.client.id:
            return 'client'
        if user.id == order.executor.id:
            return 'executor'
        await message.answer('У вас нет доступа к этому заказу')
        raise CancelHandler()


class CallbackOrderFilter(CallbackDataFilter):
    def __init__(self, factory: CallbackData, config: dict[str, str], ignore_id: bool=False):
        self.ignore_id = ignore_id
        super().__init__(factory, config)

    async def check(self, query: types.CallbackQuery):
        data = await super().check(query)
        if not data:
            return data
        data['order'] = None
        order_id = data['callback_data']['id']
        if order_id == 'null' or self.ignore_id:
            return data
        try:
            data['order'] = Order.get_by_id(order_id)
        except Order.DoesNotExist:
            await query.message.delete()
            await query.message.answer('Заказ не найден')
            raise CancelHandler()
        return data


class CallbackOrder(CallbackData):
    def filter(self, ignore_id=False, **config) -> CallbackOrderFilter:
        for key in config.keys():
            if key not in self._part_names:
                raise ValueError(f'Invalid field name {key!r}')
        return CallbackOrderFilter(self, config, ignore_id)


order_data = CallbackOrder('order', 'id', 'action')


async def send_orders(orders: list[Order], user_id) -> types.InlineKeyboardMarkup:
    if not orders:
        return await bot.send_message(user_id, 'У вас нет заказов')
    text = 'Ваши заказы: \n'
    for order in orders:
        text += (
            f'Заказ /order_{order.id}:\n'
            f'Исполнитель: {order.executor.person.real_name}\n'
            f'Заказчик: {order.client.real_name}\n'
            f'Статус заказа: {order.status}\n'
            f'Описание заказа: {order.description[:100]}{"..." if len(order.description) > 100 else ""}\n\n'
        )
    await bot.send_message(
        user_id, text
    )


async def _get_keyboard(role: str, order: Order) -> types.InlineKeyboardButton:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            'Коммментарии', callback_data=comment_data.new(order_id=order.id, action='show_comments')
        ),
        types.InlineKeyboardButton(
            'Отмена', callback_data='cancel'
        )
    )
    clients_buttons = (
        types.InlineKeyboardButton(
            'Изменить описание', callback_data=order_data.new(id=order.id, action='change_description')
        ),
    )
    executors_buttons = (
        types.InlineKeyboardButton(
            'Изменить статус', callback_data=order_data.new(id=order.id, action='change_status')
        ),
        types.InlineKeyboardButton(
            'Заказ готов!', callback_data=order_data.new(id=order.id, action='done')
        )
    )
    match role:
        case 'admin':
            keyboard.add(*clients_buttons, *executors_buttons)
        case 'client':
            keyboard.add(*clients_buttons)
        case 'executor':
            keyboard.add(*executors_buttons)
        case _:
            raise ValueError(f'The "{role}" role does not exist')
    return keyboard


async def get_order(message: types.Message, order: Order, role: str):
    keyboard = await _get_keyboard(role, order)
    text = (
        f'Заказ /order_{order.id}:\n'
        f'Исполнитель: {order.executor.person.real_name}\n'
        f'Заказчик: {order.client.real_name}\n'
        f'Статус заказа: {order.status}',
        f'Описание заказа: {order.description}\n\n'
        'Последний комментарий: \n'
        f'{order.comments.order_by(Comment.date.desc()).first() or "Нет комментариев"}'
    )
    if order.photo_file_id:
        return await message.answer_photo(
            order.photo_file_id, text,
            reply_markup=keyboard,
        )
    await message.answer(
        text,
        reply_markup=keyboard
    )


async def client_orders(call: types.CallbackQuery):
    client: Person = Person.get_by_id(call.from_user.id)
    orders = client.orders
    await send_orders(orders, client.id)
    await call.message.delete()


async def artist_orders(call: types.CallbackQuery):
    person: Person = Person.get_by_id(call.from_user.id)
    orders = person.artist.first().orders
    await send_orders(orders, person.id)
    await call.message.delete()


async def new_order(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    artist = Artist.get_by_id(callback_data['id'])
    await state.update_data({'executor': artist})
    await StateOrder.wait_description.set()
    await call.message.answer('Опишите заказ (вы можете прекрепить в описанию ОДНУ фотографию):')
    await call.message.delete()


async def order_set_description(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('Готово!', callback_data=order_data.new(id='null', action='create')),
        types.InlineKeyboardButton('Отмена', callback_data='cancel')
    )
    data = await state.get_data()
    text = (
        'Подтвердите заказ:\n'
        f'Исполнитель: {data["executor"].person.real_name}\n'
        f'Описание: {message.text or message.caption}'
    )
    await StateOrder.change_or_create.set()
    await state.update_data({
        'description': message.text or message.caption,
        'photo_file_id': message.photo[-1].file_id if message.photo else None
    })
    if message.content_type == types.ContentType.PHOTO:
        return await message.answer_photo(
            message.photo[-1].file_id, text,
            reply_markup=keyboard
        )
    await message.answer(text, reply_markup=keyboard)


async def order_change_or_create(call: types.CallbackQuery, state: FSMContext):
    order_data = await state.get_data()
    await state.finish()
    order_data.setdefault('client', call.from_user.id)
    if order_id := order_data.pop('order_id', False):
        order = Order.get_by_id(order_id)
        order.update(**order_data).execute()
    else:
        order = Order.create(**order)
    await notify(
        call.from_user.id, order, 
        (f'Заказ изменён /order_{order.id}'
        if order_id else
        f'Новый заказ /order_{order.id}')
    )
    await call.message.answer(
        'Заказ сделан, вы можете в любое время посмотреть его статус и/или изменить '
        f'описание по этой комманде /order_{order.id}.\n Нажмите /start чтобы попасть в меню.'
    )
    await call.message.delete()


async def change_description(call: types.CallbackQuery, state: FSMContext, order: Order):
    await StateOrder.wait_description.set()
    await state.update_data(dict(
        order_id=order.id,
        description=order.description,
        client=order.client,
        executor=order.executor,
        photo_file_id=order.photo_file_id
    ))
    await call.message.delete()
    await call.message.answer('Опишите заказ (вы можете прекрепить в описанию ОДНУ фотографию):')


async def change_status(call: types.CallbackQuery, state: FSMContext, order: Order):
    await StateOrder.wait_status.set()
    await state.update_data(dict(
        order_id=order.id,
        description=order.description,
        client=order.client,
        executor=order.executor,
        photo_file_id=order.photo_file_id
    ))
    await call.message.delete()
    await call.message.answer('Каким будет новый статус работы? Напишите его: ')


async def push_status(message: types.Message, state: FSMContext):
    await StateOrder.change_or_create.set()
    await state.update_data(dict(status=message.text))
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('Да', callback_data=order_data.new(id='null', action='create')),
        types.InlineKeyboardButton('Нет', callback_data='cancel')
    )
    await message.answer(
        'Изменить статус?',
        reply_markup=keyboard
    )


def register_orders_handler(dp: Dispatcher):
    dp.register_callback_query_handler(
        client_orders, lambda c: c.data == 'client_orders'
    )
    dp.register_callback_query_handler(
        artist_orders, lambda c: c.data == 'artist_orders'
    )
    dp.register_callback_query_handler(
        new_order, order_data.filter(ignore_id=True, action='new_order')
    )
    dp.register_message_handler(
        order_set_description, state=StateOrder.wait_description,
        content_types=(types.ContentType.PHOTO, types.ContentType.TEXT)
    )
    dp.register_callback_query_handler(
        order_change_or_create, order_data.filter(action='create'), state=StateOrder.change_or_create
    )
    dp.register_callback_query_handler(
        change_description, order_data.filter(action='change_description')
    )
    dp.register_callback_query_handler(
        change_status, order_data.filter(action='change_status')
    )
    dp.register_message_handler(
        push_status, state=StateOrder.wait_status
    )
    dp.register_message_handler(
        get_order, TextOrderFilter(startswith='/order_')
    )
