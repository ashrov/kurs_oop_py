""" Модели, из которых строится файл дампа """

from datetime import datetime

from pydantic import BaseModel


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
    books: list[BookIssue]


class FileModel(BaseModel):
    books: list[Book]
    readers: list[Reader]
