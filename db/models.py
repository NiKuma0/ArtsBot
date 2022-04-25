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
    status = peewee.CharField(default='Художник ещё не приступил к работе')
    photo_file_id = peewee.CharField(max_length=400, null=True)
    done = peewee.BooleanField(default=False)
    
    def __repr__(self) -> str:
        return (
            f'<{type(self).__name__} id={self.id}, '
            f'{self.description[:15]}{"..." if len(self.description) > 15 else ""}>'
        )


class Comment(BaseModel):
    date = peewee.DateTimeField()
    text = peewee.TextField()
    from_person = peewee.ForeignKeyField(Person, backref='comments')
    order = peewee.ForeignKeyField(Order, backref='comments')

    def __str__(self):
        return f'От {self.from_person.real_name}:\n- {self.text}'


class Photo(BaseModel):
    file_id = peewee.CharField(max_length=400, primary_key=True)
    artist = peewee.ForeignKeyField(Artist, backref='photos')


def create_tables():
    database.create_tables((Artist, Person, Photo, Order, Comment))
