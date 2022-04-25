import asyncio

from db.models import Person, Order
from app import bot
from config import ADMINS_NAME, TESTING


async def notify(exclude: str|int, order: Order, message: str='Новое уведомление!'):
    """Notify users"""
    if TESTING:
        return None
    users: list[Person] = []
    users.append(order.executor.person)
    users.append(order.client)
    users += list(Person.select().where(Person.name.in_(ADMINS_NAME)))
    users = filter(lambda user: user.id != exclude, users)
    return await asyncio.gather(
        *[bot.send_message(user.id, message) for user in set(users)], return_exceptions=False
    )
