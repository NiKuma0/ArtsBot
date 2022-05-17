from aiogram import Dispatcher
from .orders import register_base_handler
from .get_order import register_get_order_handler
from .new_order import register_new_orders_handler


def register_orders_handler(dp: Dispatcher):
    register_base_handler(dp)
    register_get_order_handler(dp)
    register_new_orders_handler(dp)
