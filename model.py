#! python3
import os

import peewee as pw
import playhouse.db_url as db_url

DATABASE_URL = os.environ["DATABASE_URL"]

db = db_url.connect(DATABASE_URL, sslmode="require")


class BaseModel(pw.Model):
    class Meta:
        database = db


class Sleep(BaseModel):
    date = pw.DateField(primary_key=True)
    amount = pw.SmallIntegerField()


class Out(BaseModel):
    date = pw.DateField(primary_key=True)
    amount = pw.SmallIntegerField()


class Birthday(BaseModel):
    date = pw.SmallIntegerField(primary_key=True)
    text = pw.TextField()


class Period(BaseModel):
    idate = pw.DateField()
    fdate = pw.DateField()
    text = pw.TextField()


class State(BaseModel):
    name = pw.TextField(unique=True)
    state = pw.TextField()
    date = pw.DateTimeField()


class User(BaseModel):
    username = pw.TextField(unique=True)
    password = pw.TextField()
    role = pw.SmallIntegerField()


def main():
    db.connect()
    db.create_tables([Sleep, Out, Birthday, Period, State, User])
