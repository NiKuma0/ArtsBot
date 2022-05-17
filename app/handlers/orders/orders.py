from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from app import bot
from config import PAYMENTS_TOKEN
from app.utils import notify
from db.models import Order, Photo
from app.filters.callbacks import order_data
from app.filters.states import StateOrder


async def change_description(call: types.CallbackQuery, state: FSMContext, order: Order):
    await StateOrder.wait_description.set()
    await state.update_data(
        order=order,
        client_message='Описание заказа изменено администрацией /order_{order.id}',
        executor_message='Описание заказа обновлено /order_{order.id}',
        admin_message='Описание заказа обновлено /order_{order.id}',
    )
    await call.message.delete()
    await call.message.answer('Опишите заказ (вы можете прекрепить в описанию ОДНУ фотографию):')


async def change_status(call: types.CallbackQuery, state: FSMContext, order: Order):
    await StateOrder.wait_status.set()
    await state.update_data(
        order=order,
        client_message='Новый статус заказа /order_{order.id}',
        executor_message='Статус изменён администрацией /order_{order.id}',
        admin_message='Статус заказа обновлен /order_{order.id}',
    )
    await call.message.delete()
    await call.message.answer('Каким будет новый статус работы? Напишите его: ')


async def push_status(message: types.Message, state: FSMContext):
    await StateOrder.change_or_create.set()
    order = (await state.get_data())['order']
    order.status = message.text
    await state.update_data(dict(order=order))
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('Да', callback_data=order_data.new(id='null', action='create')),
        types.InlineKeyboardButton('Нет', callback_data='cancel')
    )
    await message.answer(
        'Изменить статус?',
        reply_markup=keyboard
    )


async def order_done(call: types.CallbackQuery, state: FSMContext, order: Order):
    if order.paid:
        await call.message.edit_text(
            'Заказ уже оплачен!'
        )
    if not order.price:
        await call.message.edit_text(
            f'Сначала укажите цену в меню заказа /order_{order.id}'
        )
    await StateOrder.wait_result_photos.set()
    order.status = 'Заказ готов и ждёт оплаты'
    await state.update_data({'order': order})
    await call.message.delete()
    await call.message.answer(
        'Пришлите фото результата работы. Они будут доступны клиенту после оплаты.'
    )


async def set_result_photos(message: types.Message, state: FSMContext, album: list[types.Message]=[]):
    await StateOrder.order_done.set()
    order: Order = (await state.get_data())['order']
    photos = [
        album_message.photo[-1]
        for album_message in album
    ] or [message.photo[-1]]
    await state.update_data(result_photos=photos)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('Да', callback_data=order_data.new(order_id=order.id, action='order_done_notify')),
        types.InlineKeyboardButton('Нет', callback_data='cancel')
    )
    await message.answer(
        "Вы уверены что хотите закончить заказ?", reply_markup=keyboard
    )


async def order_done_notify(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    order: Order = state_data['order']
    order.result_photos.clear()
    order.result_photos.add(
        Photo.create_album(state_data['result_photos'])
    )
    order.save()
    price = (
        types.LabeledPrice(f'Заказ №{order.id}', order.price),
    )
    await state.finish()
    await notify(
        exclude=(order.client.id, order.executor.id),
        order=order,
        admin_message=f'Заказ готов - ждёт оплаты (/order_{order.id})'
    )
    await bot.send_invoice(
        order.client.id,
        title=f'Ваш заказ готов!',
        description=(
            f'Заказ №{order.id} готов, вы можете получить результат работы сразу после оплаты!'
        ),
        provider_token=PAYMENTS_TOKEN,
        payload=str(order.id),
        currency='rub',
        prices=price,
    )


async def wait_price(call: types.CallbackQuery, state: FSMContext, order: Order):
    await StateOrder.wait_price.set()
    await state.update_data(
        order=order,
        client_message='Установлена цена заказа /order_{order.id}',
        executor_message='Цена изменена администрацией /order_{order.id}',
        admin_message='Установлена цена заказа /order_{order.id}',
    )
    await call.message.delete()
    await call.message.answer('Какой будет цена в рублях?')
 

async def set_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
    except ValueError:
        return await message.answer(
            'Введите число'
        )
    await StateOrder.change_or_create.set()
    order: Order = (await state.get_data())['order']
    order.price = price
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('Да', callback_data=order_data.new(order_id=order.id, action='create')),
        types.InlineKeyboardButton('Нет', callback_data='cancel')
    )
    await state.update_data(order=order)
    await message.answer(
        'Это ваша цена?', reply_markup=keyboard
    )


async def successful_payment(message: types.Message):
    order_id = message.successful_payment.invoice_payload
    order: Order = Order.get_by_id(order_id)
    order.paid = True
    order.save()
    photos: list[types.PhotoSize]= [
        types.InputMedia(photo.get_as_photosize())
        for photo in order.result_photos
    ]
    await message.answer_media_group(
        photos
    )


async def pre_checkout(pre_checkout: types.PreCheckoutQuery, *args, **kwargs):
    order_id = pre_checkout.invoice_payload
    order: Order = Order.get_by_id(order_id)
    if order.paid:
        await bot.answer_pre_checkout_query(
            pre_checkout.id, ok=False, error_message='Этот заказ уже оплачен!'
        )
    await bot.answer_pre_checkout_query(
        pre_checkout.id, ok=True
    )
 

def register_base_handler(dp: Dispatcher):
    dp.register_callback_query_handler(
        change_description, order_data.filter(action='change_description')
    )
    dp.register_callback_query_handler(
        change_status, order_data.filter(action='change_status')
    )
    dp.register_message_handler(
        push_status, state=StateOrder.wait_status
    )
    dp.register_callback_query_handler(
        order_done, order_data.filter(action='done')
    )
    dp.register_message_handler(
        set_result_photos, content_types=types.ContentType.PHOTO, state=StateOrder.wait_result_photos
    )
    dp.register_callback_query_handler(
        order_done_notify, order_data.filter(action='order_done_notify'), state=StateOrder.order_done
    )
    dp.register_callback_query_handler(
        wait_price, order_data.filter(action='change_price')
    )
    dp.register_message_handler(
        set_price, state=StateOrder.wait_price
    )
    dp.register_message_handler(
        successful_payment, state='*', content_types=types.ContentType.SUCCESSFUL_PAYMENT
    )
    dp.register_pre_checkout_query_handler(
        pre_checkout, lambda query: True
    )
