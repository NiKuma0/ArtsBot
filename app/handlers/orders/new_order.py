from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from db.models import Order, Artist, Photo
from app.filters.callbacks import order_data
from app.filters.states import StateOrder
from app.utils import notify


async def new_order(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    artist = Artist.get_by_id(callback_data['order_id'])
    order = Order()
    order.executor = artist
    order.client = call.from_user.id
    await state.update_data(
        order=order,
        executor_message='У вас новый заказ /order_{order.id}',
        admin_message='Новый заказ /order_{order.id}'
    )
    await StateOrder.wait_description.set()
    await call.message.answer(
        'Опишите заказ (вы можете прекрепить в описанию ОДНУ фотографию):'
    )
    await call.message.delete()


async def order_set_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order: Order = data['order']
    order.description = message.text or message.caption
    order.expample_photo.delete() if order.expample_photo else None
    order.expample_photo = (
        Photo.from_photosize(message.photo[-1])
        if message.photo else None
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('Готово!', callback_data=order_data.new(order_id=order.id or 'null', action='create')),
        types.InlineKeyboardButton('Отмена', callback_data='cancel')
    )
    text = (
        'Подтвердите заказ:\n'
        f'Исполнитель: {order.executor.person.real_name}\n'
        f'Описание: {message.text or message.caption}'
    )
    await StateOrder.change_or_create.set()
    await state.update_data({'order': order})
    if message.content_type == types.ContentType.PHOTO:
        return await message.answer_photo(
            message.photo[-1].file_id, text,
            reply_markup=keyboard
        )
    await message.answer(text, reply_markup=keyboard)


async def order_change_or_create(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    order = state_data['order']
    await state.finish()
    order.save()
    await notify(
        call.from_user.id, order,
        state_data.get('client_message', ''),
        state_data.get('executor_message', ''),
        state_data.get('admin_message', ''),
    )
    await call.message.answer(
        'Заказ сделан, вы можете в любое время посмотреть его статус и/или изменить '
        f'описание по этой комманде /order_{order.id}.\n Нажмите /start чтобы попасть в меню.'
    )
    await call.message.delete()
    return order


def register_new_orders_handler(dp: Dispatcher):
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
