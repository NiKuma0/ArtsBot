from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from db.models import Order, Comment
from app.utils import notify
from app.filters.states import NewComment
from app.filters.callbacks import comment_data
from app import bot


async def show_comments(call: types.CallbackQuery, order: Order):
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


async def new_comment(call: types.CallbackQuery, order: Order, state: FSMContext):
    await state.update_data({'order': order})
    await call.message.delete()
    await call.message.answer('Напишите комментарий:')
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
    await notify(
        message.from_user.id, data['order'], 
        'Новый комментарий /order_{order.id}',
        'Новый комментарий /order_{order.id}',
        'Новый комментарий /order_{order.id}',
    )
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
