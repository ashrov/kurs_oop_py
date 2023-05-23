from typing import Any, Callable
from abc import abstractmethod
from functools import wraps

from sqlalchemy import Column, String, BigInteger, Integer, SmallInteger, Engine, create_engine, Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from .config_models import DbConfig


_engine: Engine

Base = declarative_base()


def init_db(db_config: DbConfig):
    global _engine

    _engine = create_engine(db_config.url)
    sessionmaker(bind=_engine)
    Base.metadata.create_all(bind=_engine)


def get_database(f: Callable):
    """ Декоратор, который подсовывает в аргументы оборачиваемой функции сессию базы данных """

    @wraps(f)
    def wrapper(*args, **kwargs):

        with Session(bind=_engine) as db:
            result = f(*args, **kwargs, db=db)

        return result

    return wrapper


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

    readers = relationship("Reader", secondary="book_to_reader", back_populates="books")

    @staticmethod
    def get_table_name() -> str:
        return "Книги"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Код", "Название", "Автор", "Доступно", "Всего"]

    def get_values(self) -> dict[str, Any]:
        return {
            "Код": self.code,
            "Название": self.name,
            "Автор": self.author,
            "Доступно": f"{self.get_available_count()} шт.",
            "Всего": f"{self.count} шт."
        }

    def get_available_count(self) -> int:
        return self.count - len(self.readers)


class Reader(TableViewable):
    __tablename__ = "readers"

    id = Column(BigInteger(), primary_key=True)
    firstname = Column(String(64))
    lastname = Column(String(64))
    phone = Column(String(12), unique=True, nullable=False)

    books = relationship("Book", secondary="book_to_reader", back_populates="readers")

    @staticmethod
    def get_table_name() -> str:
        return "Читатели"

    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Имя", "Фамилия", "Номер телефона", "Книг взято"]

    def get_values(self) -> dict[str, Any]:
        return {
            "Имя": self.firstname,
            "Фамилия": self.lastname,
            "Номер телефона": self.phone,
            "Книг взято": f"{len(self.books)} шт.",
        }


class BookToReader(Base):
    __tablename__ = "book_to_reader"

    book_id = Column(BigInteger, ForeignKey("books.id"), primary_key=True)
    reader_id = Column(BigInteger, ForeignKey("readers.id"), primary_key=True)
