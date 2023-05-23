""" Модели, из которых строится файл дампа """

from pydantic import BaseModel


class Book(BaseModel):
    code: str
    name: str
    author: str
    count: int | None


class Reader(BaseModel):
    firstname: str
    lastname: str
    phone: str
    books: list[str]


class FileModel(BaseModel):
    books: list[Book]
    readers: list[Reader]
