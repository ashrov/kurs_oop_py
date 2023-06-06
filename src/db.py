import enum
from typing import Any, Callable
from abc import abstractmethod, ABC
from functools import wraps
from datetime import datetime

import sqlalchemy as sql
from sqlalchemy import (
    Column, String, BigInteger, Integer, Engine, create_engine, DateTime, ForeignKey, ColumnElement, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from .config_models import DbConfig


_engine: Engine

Base = declarative_base()


def init_db(db_config: DbConfig):
    global _engine

    _engine = create_engine(db_config.url)
    sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(bind=_engine)


def wrap_with_database(f: Callable):
    """ Декоратор, который подсовывает в аргументы оборачиваемой функции сессию базы данных """

    @wraps(f)
    def wrapper(*args, **kwargs):

        with Session(bind=_engine, expire_on_commit=False) as db:
            result = f(*args, **kwargs, db=db)

        return result

    return wrapper


@wrap_with_database
def add_event_to_history(event_type: "EventType", comment: str = "", db: Session = None):
    event = History(event_type=event_type, comment=comment)

    db.add(event)
    db.commit()


class TableViewable(Base):
    __abstract__ = True

    @staticmethod
    @abstractmethod
    def get_table_name() -> str:
        ...

    @staticmethod
    @abstractmethod
    def get_table_fields() -> list[str]:
        ...

    @staticmethod
    @abstractmethod
    def get_search_where_clause(str_to_search: str = "") -> ColumnElement | None:
        ...

    @abstractmethod
    def get_values(self) -> dict[str, Any]:
        ...


class Sortable(TableViewable):
    __abstract__ = True

    @staticmethod
    @abstractmethod
    def get_sort_fields() -> dict[str, Any]:
        ...


class Book(Sortable):
    __tablename__ = "books"

    id = Column(BigInteger(), primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    author = Column(String(128), nullable=False)
    count = Column(Integer(), default=0, nullable=False)

    readers_associations = relationship("BookToReader", back_populates="book", cascade="all, delete")

    @staticmethod
    def get_table_name() -> str:
        return "Книги"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Код", "Название", "Автор", "Доступно", "Всего"]

    @staticmethod
    def get_search_where_clause(str_to_search: str = "") -> ColumnElement | None:
        if not str_to_search:
            return None

        clause = sql.or_(
            Book.code.contains(str_to_search),
            Book.name.contains(str_to_search),
            Book.author.contains(str_to_search),
        )

        return clause

    def get_values(self) -> dict[str, Any]:
        return {
            "Код": self.code,
            "Название": self.name,
            "Автор": self.author,
            "Доступно": f"{self.get_available_count()} шт.",
            "Всего": f"{self.count} шт."
        }

    def get_available_count(self) -> int:
        return self.count - self.get_taken_count()

    def get_taken_count(self) -> int:
        return len(self.readers_associations)

    @staticmethod
    def get_sort_fields() -> dict[str, Any]:
        return {
            "Код": Book.code,
            "Название": Book.name,
            "Автор": Book.author,
            "Количество": Book.count
        }


class Reader(Sortable):
    __tablename__ = "readers"

    id = Column(BigInteger(), primary_key=True)
    firstname = Column(String(64))
    lastname = Column(String(64))
    phone = Column(String(12), unique=True, nullable=False)

    books_associations = relationship("BookToReader", back_populates="reader")

    @staticmethod
    def get_table_name() -> str:
        return "Читатели"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Имя", "Фамилия", "Номер телефона", "Книг взято"]

    @staticmethod
    def get_search_where_clause(str_to_search: str = "") -> ColumnElement | None:
        if not str_to_search:
            return None

        clause = sql.or_(
            Reader.phone.contains(str_to_search),
            Reader.firstname.contains(str_to_search),
            Reader.lastname.contains(str_to_search)
        )

        return clause

    def get_values(self) -> dict[str, Any]:
        return {
            "Имя": self.firstname,
            "Фамилия": self.lastname,
            "Номер телефона": self.phone,
            "Книг взято": f"{len(self.books_associations)} шт.",
        }

    @staticmethod
    def get_sort_fields() -> dict[str, Any]:
        return {
            "Имя": Reader.firstname,
            "Фамилия": Reader.lastname,
        }


class BookToReader(Sortable):
    __tablename__ = "book_to_reader"

    id = Column(BigInteger, primary_key=True)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"))
    reader_id = Column(BigInteger, ForeignKey("readers.id", ondelete="RESTRICT"))
    issue_date = Column(DateTime, default=datetime.now(), nullable=False)

    book = relationship("Book", back_populates="readers_associations")
    reader = relationship("Reader", back_populates="books_associations")

    @staticmethod
    def get_table_name() -> str:
        return "Взятые книги"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Код книги", "Номер телефона", "Дата выдачи"]

    @staticmethod
    def get_search_where_clause(str_to_search: str = "") -> ColumnElement | None:
        if not str_to_search:
            return None

        clause = sql.or_(
            BookToReader.book.has(Book.code.contains(str_to_search)),
            BookToReader.reader.has(Reader.phone.contains(str_to_search)),
        )

        return clause

    def get_values(self) -> dict[str, Any]:
        return {
            "Код книги": self.book.code,
            "Номер телефона": self.reader.phone,
            "Дата выдачи": self.issue_date
        }

    @staticmethod
    def get_sort_fields() -> dict[str, Any]:
        return {
            "Дата выдачи": BookToReader.issue_date
        }


class EventType(enum.Enum):
    BOOK_TAKEN = "Читатель взял книгу"
    BOOK_RETURNED = "Книга возвращена"
    NEW_READER = "Новый читатель"
    READER_LEFT = "Читатель удалён"
    BOOK_WRITTEN_OFF = "Экземпляр списан"


class History(Sortable):
    __tablename__ = "history"

    id = Column(BigInteger, primary_key=True)

    time = Column(DateTime, default=datetime.now())
    event_type = Column(sql.Enum(EventType), nullable=False)
    comment = Column(String(256), default="")

    @staticmethod
    def get_table_name() -> str:
        return "История"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Время", "Событие", "Комментарий"]

    def get_values(self) -> dict[str, Any]:
        return {
            "Время": self.time,
            "Событие": self.event_type.value,
            "Комментарий": self.comment
        }

    @staticmethod
    def get_search_where_clause(str_to_search: str = "") -> ColumnElement | None:
        return None

    @staticmethod
    def get_sort_fields() -> dict[str, Any]:
        return {
            "Время": History.time,
            "Событие": History.event_type
        }


# ----------- Вспомогательные модели ------------
#   Могут понадобиться для промежуточных таблиц

class TakenBook(BookToReader):
    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Код", "Название", "Автор", "Телефон читателя", "Дата выдачи"]

    def get_values(self) -> dict[str, Any]:
        return {
            "Код": self.book.code,
            "Название": self.book.name,
            "Автор": self.book.author,
            "Телефон читателя": self.reader.phone,
            "Дата выдачи": self.issue_date
        }

    @staticmethod
    def get_search_where_clause(str_to_search: str = "") -> ColumnElement | None:
        if not str_to_search:
            return None

        clause = sql.or_(
            BookToReader.book.has(Book.code.contains(str_to_search)),
            BookToReader.book.has(Book.name.contains(str_to_search)),
            BookToReader.book.has(Book.author.contains(str_to_search)),
            BookToReader.reader.has(Reader.phone.contains(str_to_search))
        )

        return clause