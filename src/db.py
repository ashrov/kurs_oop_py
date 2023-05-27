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


def get_database(f: Callable):
    """ Декоратор, который подсовывает в аргументы оборачиваемой функции сессию базы данных """

    @wraps(f)
    def wrapper(*args, **kwargs):

        with Session(bind=_engine, expire_on_commit=False) as db:
            result = f(*args, **kwargs, db=db)

        return result

    return wrapper


def add_it_to_history(event_type: "EventType"):
    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result and result.value == 1:
                with Session(bind=_engine, expire_on_commit=False) as db:
                    db.add(History(event_type=event_type))
                    db.commit()

            return result
        return wrapper
    return decorator


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

    @get_database
    def delete(self, db: Session) -> None:
        db.delete(self)
        db.commit()


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
        return self.count - len(self.readers_associations)

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
            "Код книги": BookToReader.book.has(Book.code),
            "Дата выдачи": BookToReader.issue_date
        }


class EventType(enum.Enum):
    BOOK_TAKEN = "Book taken"
    BOOK_RETURNED = "Book returned"
    NEW_READER = "New reader"


class History(Sortable):
    __tablename__ = "history"

    id = Column(BigInteger, primary_key=True)

    time = Column(DateTime, default=datetime.now())
    event_type = Column(sql.Enum(EventType), nullable=False)

    @staticmethod
    def get_table_name() -> str:
        return "История"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Время", "Событие"]

    def get_values(self) -> dict[str, Any]:
        return {
            "Время": self.time,
            "Событие": self.event_type
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
