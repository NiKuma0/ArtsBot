from aiogram import types, Dispatcher
from aiogram.dispatcher import filters

from db.models import Artist, Person
from app import bot
from config import ADMINS_NAME


def admin_filter(message: types.Message):
    return message.from_user.username in ADMINS_NAME


async def admin_start(message: types.Message,):
    await message.answer(
        'Приветствую! Чтобы посмотреть доступные '
        'команды для админа, нажмите /help'
    )


async def add_artist(message: types.Message, command: filters.Command.CommandObj):
    if not command.args:
        return await message.answer(
            'Передайте имя пользавателя\n'
            '```\n\/add\_artist @<username>```',
            parse_mode='markdownV2'
        )
    username = command.args.removeprefix('@')
    try:
        person = Person.get(Person.name == username)
    except Person.DoesNotExist:
        return await message.answer('Пользаватель не найден!')
    Artist.create(person=person)
    await message.answer('Готово!')


async def delete_artist(message: types.Message, command: filters.Command.CommandObj):
    if not command.args:
        return await message.answer(
            'Передайте имя пользавателя\n'
            '```\n\/add\_artist @<username>```',
            parse_mode='markdownV2'
        )
    username = command.args.removeprefix('@')
    try:
        artist = Artist.select().join(Person).get(Person.name == username)
    except Person.DoesNotExist:
        return await message.answer('Пользаватель не найден!')
    artist.delete()
    await message.answer('Готово!')


async def bot_help(message: types.Message):
    text = (
        '\/help \- Вызывает это сообщение\.\n'
        '\/reg\_user \- Добавляет вас в БД\.\n'
        'Команды для Админа:\n'
        '\/add\_artist \- Делает пользавателя Художником\.\n'
        '```\n\/add\_artist @<username>```\n'
        '*Чтобы комманда сработала, нужно чтобы пользаватель был в БД\.* '
        'Для этого он должен написать боту комманду \/reg\_user'
    )
    await message.answer(
        text,
        parse_mode="MarkdownV2"
    )


def register_admin_handler(dp: Dispatcher):
    dp.register_message_handler(bot_help, commands='help')
    dp.register_message_handler(add_artist, filters.Command('add_artist'), admin_filter)
    dp.register_message_handler(delete_artist, filters.Command('delete_artist'), admin_filter)
