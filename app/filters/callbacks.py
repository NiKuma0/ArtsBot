from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.utils.callback_data import CallbackData, CallbackDataFilter

from db.models import Order


class CallbackOrderFilter(CallbackDataFilter):
    def __init__(self, factory: CallbackData,
                 config: dict[str, str],
                 ignore_id: bool = False):
        self.ignore_id = ignore_id
        super().__init__(factory, config)

    async def check(self, query: types.CallbackQuery):
        data = await super().check(query)
        if not data:
            return
        data['order'] = None
        order_id = data['callback_data']['order_id']
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


order_data = CallbackOrder('order', 'order_id', 'action')
comment_data = CallbackOrder('comments', 'order_id', 'action')
artist_callback = CallbackData('artist', 'index', 'action')
