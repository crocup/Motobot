import os
from peewee import *

database = SqliteDatabase(os.path.normpath(os.path.join(os.path.dirname(__file__), 'Bike_db.sqlite')))  # https://habr.com/ru/post/322086/


# Определяем базовую модель о которой будут наследоваться остальные
class BaseModel(Model):
    class Meta:
        database = database  # соединение с базой, из шаблона выше


# Определяем модель исполнителя
class Bike(BaseModel):
    user_id = AutoField(column_name='UserId')
    user_uid = TextField(column_name='UserUid')
    name_bike = TextField(column_name='Name')
    link_bike = TextField(column_name='Link')
    link_hash = TextField(column_name='Hash')

    class Meta:
        table_name = 'Bike'


Bike.create_table()
