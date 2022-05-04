from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.filters import Text

from db.models import Order
from config import ADMINS_NAME


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
