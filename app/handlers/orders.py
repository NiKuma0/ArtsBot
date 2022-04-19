from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.utils.callback_data import CallbackData

from db.models import Person, Order, Artist, Comment
from .comments import comment_data
from app import bot
from app.tools import notify
from config import ADMINS_NAME


order_data = CallbackData('order', 'id', 'action')


class NewOrder(StatesGroup):
    wait_description = State()
    done = State()


class OrderFilter(Text):
    async def check(self, obj: types.Message):
        result = await super().check(obj)
        if not result:
            return result
        order = await self.get_order(obj)
        await self.has_perm(obj, order)
        return {'order': order}
    
    async def get_order(self, message: types.Message) -> Order:
        order_id = message.text.removeprefix(self.startswith[0])
        try:
            order: Order = Order.get_by_id(order_id)
        except Order.DoesNotExist:
            await message.answer('Заказ не найден!')
            raise CancelHandler()
        return order
    
    async def has_perm(self, message: types.Message, order: Order):
        user = message.from_user
        if user.id in (order.client, order.executor) or user.username in ADMINS_NAME:
            return True
        await message.answer('У вас нет доступа к этому заказу')
        raise CancelHandler



async def send_orders(orders: list[Order], user_id) -> types.InlineKeyboardMarkup:
    if not orders:
        return bot.send_message(user_id, 'У вас нет заказов')
    text = 'Ваши заказы: \n'
    for order in orders:
        text += (
            f'Заказ /order_{order.id}:\n'
            f'Исполнитель: {order.executor.person.real_name}\n'
            f'Заказчик: {order.client.real_name}\n'
            f'Описание заказа: {order.description}\n\n'
        )
    await bot.send_message(
        user_id, text
    )


async def get_order(message: types.Message, order: Order):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            'Коммментарии', callback_data=comment_data.new(order_id=order.id, action='show_comments')
        ),
    )
    await message.answer(
        f'Заказ /order_{order.id}:\n'
        f'Исполнитель: {order.executor.person.real_name}\n'
        f'Заказчик: {order.client.real_name}\n'
        f'Описание заказа: {order.description}\n\n'
        'Последний комментарий: \n'
        f'{order.comments.order_by(Comment.date.desc()).first()}',
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
    keyboard = await send_orders(orders, person.id)
    await call.message.edit_text(
        'Ваши заказы:', reply_markup=keyboard
    )


async def new_order(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    artist = Artist.get_by_id(callback_data['id'])
    await state.update_data({'artist': artist})
    await NewOrder.wait_description.set()
    await call.message.answer('Опишите заказ:')
    await call.message.delete()


async def new_order_set_description(message: types.Message, state: FSMContext):
    await state.update_data({'description': message.text})
    data = await state.get_data()
    await NewOrder.done.set()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('Готов!', callback_data=order_data.new(id='null', action='done')),
        types.InlineKeyboardButton('Отмена', callback_data='cancel')
    )
    await message.answer(
        'Подтвердите заказ:\n'
        f'Исполнитель: {data["artist"].person.real_name}\n'
        f'Описание: {message.text}',
        reply_markup=keyboard
    )


async def new_order_done(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    order = Order.create(
        description=data['description'],
        client=call.from_user.id,
        executor=data['artist'],
    )
    await notify(call.from_user.id, order, f'Новый заказ /order_{order.id}')
    await call.message.answer('Готово! Нажмите /start чтобы попасть в меню')
    await call.message.delete()


def register_orders_handler(dp: Dispatcher):
    dp.register_callback_query_handler(
        client_orders, lambda c: c.data == 'client_orders'
    )
    dp.register_callback_query_handler(
        artist_orders, lambda c: c.data == 'artist_orders'
    )
    dp.register_callback_query_handler(
        new_order, order_data.filter(action='new_order')
    )
    dp.register_message_handler(
        new_order_set_description, state=NewOrder.wait_description
    )
    dp.register_callback_query_handler(
        new_order_done, order_data.filter(action='done'), state=NewOrder.done
    )
    dp.register_message_handler(
        get_order, OrderFilter(startswith='/order_')
    )
