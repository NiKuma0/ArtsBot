import datetime

import peewee
from aiogram.types import PhotoSize

from db import BaseModel, database


class Photo(BaseModel):
    file_id = peewee.TextField()
    file_unique_id = peewee.CharField()
    width = peewee.SmallIntegerField()
    height = peewee.SmallIntegerField()
    file_size = peewee.IntegerField()

    @classmethod
    def from_photosize(cls, photosize: PhotoSize, create=True):
        photo = cls(
            **dict(photosize)
        )
        photo.save() if create else None
        return photo

    @classmethod
    def create_album(cls, album: list[PhotoSize]):
        return [cls.from_photosize(photosize) for photosize in album]

    def get_as_photosize(self) -> PhotoSize:
        return PhotoSize(
            file_id=self.file_id,
            file_unique_id=self.file_unique_id,
            width=self.width,
            height=self.height,
            file_size=self.file_size,
        )


class Person(BaseModel):
    id = peewee.PrimaryKeyField()
    name = peewee.CharField(unique=True)
    real_name = peewee.CharField()

    def __repr__(self) -> str:
        return f'<{type(self).__name__} @{self.name}>'


class Artist(BaseModel):
    description = peewee.TextField(null=True)
    person = peewee.ForeignKeyField(Person, backref='artist', unique=True)
    photos = peewee.ManyToManyField(Photo, backref='artist',)

    def __repr__(self) -> str:
        return f'<{type(self).__name__} @{self.person.name}>'


ArtistPhotos = Artist.photos.get_through_model()


class Order(BaseModel):
    date = peewee.DateField(default=datetime.datetime.now)
    description = peewee.TextField()
    client = peewee.ForeignKeyField(Person, backref='orders')
    executor = peewee.ForeignKeyField(Artist, backref='orders')
    status = peewee.CharField(default='Художник ещё не приступил к работе')
    price = peewee.SmallIntegerField(null=True)
    paid = peewee.BooleanField(default=False)
    expample_photo = peewee.ForeignKeyField(Photo, backref='order_example_photo', null=True)
    result_photos = peewee.ManyToManyField(Photo, backref='order_result_photos',)

    @property
    def done(self) -> bool:
        return self.result_photos.exists()
 
    def __repr__(self) -> str:
        return (
            f'<{type(self).__name__} id={self.id}, '
            f'{self.description[:15]}{"..." if len(self.description) > 15 else ""}>'
        )


OrderResultPhotos = Order.result_photos.get_through_model()


class Comment(BaseModel):
    date = peewee.DateTimeField()
    text = peewee.TextField()
    from_person = peewee.ForeignKeyField(Person, backref='comments')
    order = peewee.ForeignKeyField(Order, backref='comments')

    def __str__(self):
        return f'От {self.from_person.real_name}:\n- {self.text}'


def create_tables():
    database.create_tables((
        Artist, Person, Photo, Order,
        Comment, ArtistPhotos, OrderResultPhotos,
    ))
