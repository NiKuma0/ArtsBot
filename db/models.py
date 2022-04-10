import datetime

import peewee

from db import BaseModel, database


class Person(BaseModel):
    id = peewee.PrimaryKeyField()
    name = peewee.CharField(unique=True)
    real_name = peewee.CharField()

    def __repr__(self) -> str:
        return f'<{type(self).__name__} @{self.name}>'


class Artist(BaseModel):
    description = peewee.TextField(null=True)
    person = peewee.ForeignKeyField(Person, backref='artist', unique=True)

    def __repr__(self) -> str:
        return f'<{type(self).__name__} @{self.person.name}>'


class Order(BaseModel):
    date = peewee.DateField(default=datetime.datetime.now)
    description = peewee.TextField()
    client = peewee.ForeignKeyField(Person, backref='orders')
    executor = peewee.ForeignKeyField(Artist, backref='orders')
    status = peewee.CharField(null=True)
    done = peewee.BooleanField(default=False)


class Comment(BaseModel):
    date = peewee.DateTimeField()
    text = peewee.TextField()
    from_person = peewee.ForeignKeyField(Person, backref='comments')
    order = peewee.ForeignKeyField(Order, backref='comments')


class Message(BaseModel):
    text = peewee.TextField()
    from_person = peewee.ForeignKeyField(Person, backref='messages')
    date = peewee.DateTimeField()
    read = peewee.BooleanField(default=False)

    def __repr__(self) -> str:
        return f'<{type(self).__name__} {self.user.name} to {self.artist.person.name}>'


def create_tables():
    database.create_tables((Artist, Person, Message, Order, Comment))
