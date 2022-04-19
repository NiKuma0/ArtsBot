from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from db.models import Order, Comment
from app.tools import notify
from app import bot


comment_data = CallbackData('comments', 'order_id', 'action')


class NewComment(StatesGroup):
    wait_text = State()


async def show_comments(call: types.CallbackQuery, callback_data: dict):
    try:
        order = Order.get_by_id(callback_data['order_id'])
    except Order.DoesNotExist:
        return await call.answer('Заказ не найден')
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            'Комментировать', callback_data=comment_data.new(order_id=order.id, action='new_comment')
        )
    )
    if not order.comments:
        text = 'Комментариев нет'
    else:
        text = '\n\n'.join(list(map(str, order.comments)))
    await call.message.delete()
    await call.message.answer(
        text, reply_markup=keyboard
    )


async def new_comment(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    order = Order.get_by_id(callback_data['order_id'])
    await state.update_data({'order': order})
    await call.message.answer('Напишите: ')
    await NewComment.wait_text.set()


async def push_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    Comment.create(
        date=message.date,
        text=message.text,
        from_person=message.from_user.id,
        order=data['order']
    )
    await notify(message.from_user.id, data['order'], f'Новый комментарий /order_{data["order"].id}')
    await message.answer('Готово! /start')


def register_comments_handler(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_comments, comment_data.filter(action='show_comments')
    )
    dp.register_callback_query_handler(
        new_comment, comment_data.filter(action='new_comment')
    )
    dp.register_message_handler(
        push_comment, state=NewComment.wait_text
    )
