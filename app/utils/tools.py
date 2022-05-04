import asyncio

from db.models import Person, Order
from app import bot
from config import ADMINS_NAME, TESTING


async def notify(exclude: list[str|int]|str|int, order: Order, client_message=None, executor_message=None, admin_message=None):
    """Notify users"""
    if TESTING:
        return None
    if not isinstance(exclude, list):
        exclude = [exclude]
    await bot.send_message(
        order.client, client_message.format(order=order),
    ) if order.client.id not in exclude else None
    await bot.send_message(
        order.executor, executor_message.format(order=order)
    ) if order.executor.id not in exclude else None
    users += list(Person.select().where(Person.name.in_(ADMINS_NAME)))
    users = filter(lambda user: user.id not in exclude, users)
    return await asyncio.gather(
        *[bot.send_message(user.id, admin_message) for user in set(users)],
        return_exceptions=False
    )
