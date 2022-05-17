import asyncio

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from db.models import Person


class UserUpdate(BaseMiddleware):
    """Update the user if username has been changed."""
    async def on_process_update(self, update: types.Update, data: dict):
        user: types.User = None
        match update:
            case types.Update(message=message) if message:
                user = message.from_user
            case types.Update(callback_query=call) if call:
                user = call.from_user
            case types.Update(pre_checkout=pre_checkout) if pre_checkout:
                user = pre_checkout.from_user
            case _:
                return
        try:
            person = Person.get_by_id(user.id) 
        except Person.DoesNotExist:
            person = Person.create(
                id=user.id,
                name=user.username,
                real_name=user.full_name,
            )
        else:
            if person.name != user.username:
                person.name = user.username
                person.save()
        data['person'] = person
        

class AlbumMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data: dict = {}

    def __init__(self, latency: float = 0.01):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            return

        extra = self.album_data.setdefault(message.media_group_id, [])
        if extra:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()
        
        self.album_data[message.media_group_id] = [message]
        await asyncio.sleep(self.latency)
        message.conf["is_last"] = True
        data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict):
        """Clean up after handling our album."""
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]
