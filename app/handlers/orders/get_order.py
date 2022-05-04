from aiogram import types, Dispatcher

from db.models import Person, Order, Comment
from app.filters.callbacks import comment_data, order_data
from app.filters.message import TextOrderFilter
from app import bot


async def send_orders(orders: list[Order],
                      user_id) -> types.InlineKeyboardMarkup:
    if not orders:
        return await bot.send_message(user_id, 'У вас нет заказов')
    text = 'Ваши заказы: \n'
    for order in orders:
        text += (
            f'Заказ /order_{order.id}:\n'
            f'Исполнитель: {order.executor.person.real_name}\n'
            f'Заказчик: {order.client.real_name}\n'
            f'Статус заказа: {order.status}\n'
            f'Описание заказа: {order.description[:100]}'
            f'{"..." if len(order.description) > 100 else ""}\n\n'
        )
    await bot.send_message(
        user_id, text
    )


async def _get_keyboard(role: str, order: Order) -> types.InlineKeyboardButton:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            'Коммментарии',
            callback_data=comment_data.new(order_id=order.id, action='show_comments')
        ),
    )
    clients_buttons = (
        types.InlineKeyboardButton(
            'Изменить описание',
            callback_data=order_data.new(order_id=order.id, action='change_description')
        ),
    )

    executors_buttons = (
        types.InlineKeyboardButton(
            'Изменить статус',
            callback_data=order_data.new(order_id=order.id, action='change_status')
        ),
        types.InlineKeyboardButton(
            'Заказ готов!',
            callback_data=order_data.new(order_id=order.id, action='done')
        ),
        types.InlineKeyboardButton(
            'Установить цену',
            callback_data=order_data.new(order_id=order.id, action='change_price')
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
            raise ValueError(f'The role "{role}" does not exist')
    return keyboard


async def get_order(message: types.Message, order: Order, role: str):
    keyboard = await _get_keyboard(role, order)
    text = (
        f'Заказ /order_{order.id}:\n'
        f'Исполнитель: {order.executor.person.real_name}\n'
        f'Заказчик: {order.client.real_name}\n'
        f'Статус заказа: {order.status}\n'
        f'Цена заказа: {order.price or "Не указана"}\n'
        f'Описание заказа: {order.description}\n\n'
        'Последний комментарий: \n' + (
            last_comment.text
            if (last_comment := order.comments.order_by(Comment.date.desc()).first())
            else 'Нет комментариев'
        )
    )
    if order.expample_photo:
        return await message.answer_photo(
            order.expample_photo.file_id, text,
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

def register_get_order_handler(dp: Dispatcher):
    dp.register_callback_query_handler(
        client_orders, lambda c: c.data == 'client_orders'
    )
    dp.register_callback_query_handler(
        artist_orders, lambda c: c.data == 'artist_orders'
    )
    dp.register_message_handler(
        get_order, TextOrderFilter(startswith='/order_')
    )
