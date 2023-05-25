import enum
from typing import Any, Callable
from abc import abstractmethod
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


class Book(TableViewable):
    __tablename__ = "books"

    id = Column(BigInteger(), primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    author = Column(String(128), nullable=False)
    count = Column(Integer(), default=0, nullable=False)

    authors = relationship("Author", secondary="book_to_author", back_populates="books", uselist=True)
    readers_associations = relationship("BookToReader", back_populates="book", cascade="all, delete-orphan")

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


class Reader(TableViewable):
    __tablename__ = "readers"

    id = Column(BigInteger(), primary_key=True)
    firstname = Column(String(64))
    lastname = Column(String(64))
    phone = Column(String(12), unique=True, nullable=False)

    books_associations = relationship("BookToReader", back_populates="reader", cascade="all, delete-orphan")

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


class Author(TableViewable):
    __tablename__ = "authors"

    id = Column(BigInteger, primary_key=True)
    firstname = Column(String(64))
    lastname = Column(String(64))
    patronymic = Column(String(64))

    books = relationship("Book", secondary="book_to_author", back_populates="authors", uselist=True)

    __table_args__ = (
        UniqueConstraint("firstname", "lastname", "patronymic"),
    )

    @staticmethod
    def get_table_name() -> str:
        return "Авторы"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Имя", "Фамилия", "Отчество"]

    @staticmethod
    def get_search_where_clause(str_to_search: str = "") -> ColumnElement | None:
        if not str_to_search:
            return None

        clause = sql.or_(
            Author.firstname.contains(str_to_search),
            Author.lastname.contains(str_to_search),
            Author.patronymic.contains(str_to_search),
        )

        return clause

    def get_values(self) -> dict[str, Any]:
        return {
            "Имя": self.firstname,
            "Фамилия": self.lastname,
            "Отчество": self.patronymic
        }


class BookToReader(TableViewable):
    __tablename__ = "book_to_reader"

    id = Column(BigInteger, primary_key=True)
    book_id = Column(BigInteger, ForeignKey("books.id"))
    reader_id = Column(BigInteger, ForeignKey("readers.id"))
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


class BookToAuthor(Base):
    __tablename__ = "book_to_author"

    book_id = Column(BigInteger, ForeignKey("books.id"), primary_key=True)
    author_id = Column(BigInteger, ForeignKey("authors.id"), primary_key=True)


class EventType(enum.Enum):
    BOOK_TAKEN = "Book taken"
    BOOK_RETURNED = "Book returned"
    NEW_READER = "New reader"


class History(TableViewable):
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
