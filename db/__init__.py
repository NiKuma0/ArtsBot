import peewee


database = peewee.SqliteDatabase('sqlite/db.sqlite')


class BaseModel(peewee.Model):
    class Meta:
        database = database

