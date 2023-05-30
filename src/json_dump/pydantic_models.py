""" Модели, из которых строится файл дампа """

from datetime import datetime

from pydantic import BaseModel

from ..db import EventType


class Book(BaseModel):
    code: str
    name: str
    author: str
    count: int | None


class BookIssue(BaseModel):
    book_code: str
    issue_date: datetime


class Reader(BaseModel):
    firstname: str
    lastname: str
    phone: str
    books: list[BookIssue] = list()


class Event(BaseModel):
    event_type: EventType
    time: datetime
    comment: str = ""


class FileModel(BaseModel):
    books: list[Book] = list()
    readers: list[Reader] = list()
    history: list[Event] = list()
