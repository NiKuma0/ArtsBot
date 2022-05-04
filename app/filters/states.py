from aiogram.dispatcher.filters.state import State, StatesGroup


class NewComment(StatesGroup):
    wait_text = State()


class SetProfile(StatesGroup):
    name = State()
    description = State()
    photos = State()
    wait_done = State()


class MessageAnswer(StatesGroup):
    answer = State()


class AddPhoto(StatesGroup):
    wait_photo = State()


class StateOrder(StatesGroup):
    wait_description = State()
    wait_status = State()
    wait_result_photos = State()
    wait_price = State()
    order_done = State()
    change_or_create = State()
