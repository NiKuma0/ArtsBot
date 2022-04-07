import peewee


database = peewee.SqliteDatabase('bot.db')


class BaseModel(peewee.Model):
    class Meta:
        database = database

