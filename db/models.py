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


class Message(BaseModel):
    text = peewee.TextField()
    user = peewee.ForeignKeyField(Person, backref='messages')
    artist = peewee.ForeignKeyField(Artist, backref='messages')
    date = peewee.DateTimeField()


def create_tables():
    database.create_tables((Artist, Person, Message))
