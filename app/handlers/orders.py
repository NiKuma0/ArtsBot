from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.utils.callback_data import CallbackData

from db.models import Person, Order, Artist
from .comments import comment_data
from app import bot


order_data = CallbackData('order', 'id', 'action')


class NewOrder(StatesGroup):
    wait_description = State()
    done = State()


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


async def get_order(message: types.Message, *args):
    order_id = message.text.removeprefix('/order_')
    order = Order.get_by_id(order_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            'Коммментарии', callback_data=comment_data.new(order_id=order_id, action='show_comments')
        ),
    )
    await message.answer(
        f'Заказ /order_{order.id}:\n'
        f'Исполнитель: {order.executor.person.real_name}\n'
        f'Заказчик: {order.client.real_name}\n'
        f'Описание заказа: {order.description}\n\n'
        f'Последний комментарий :',
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
    if not orders:
        return await call.answer('У вас нет заказов')
    keyboard = await send_orders(orders)
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
    Order.create(
        description=data['description'],
        client=call.from_user.id,
        executor=data['artist'],
    )
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
        get_order, Text(startswith='/order_')
    )
