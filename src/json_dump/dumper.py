from logging import getLogger

from . import pydantic_models
from .. import db as database
from ..interface import ErrorNotification


logger = getLogger(__name__)


class Dumper:
    """ Класс для взаимодействия с файлами дампов """

    @staticmethod
    @database.get_database
    def dump_to_file(filepath: str, db: database.Session = None):
        """
        Экспорт данных их бд в файл в формате json.

        :param filepath: Путь до файла
        :param db: Сессия базы данных
        """

        logger.debug("Collect dump data")
        books = [pydantic_models.Book(**vars(db_book)) for db_book in db.query(database.Book).all()]

        db_readers = db.query(database.Reader).all()
        pydantic_readers = list()
        for i, db_reader in enumerate(db_readers):
            reader_books = [pydantic_models.BookIssue(book_code=association.book.code, issue_date=association.issue_date)
                            for association in db_reader.books_associations]
            pydantic_reader = pydantic_models.Reader(firstname=db_reader.firstname,
                                                     lastname=db_reader.lastname,
                                                     phone=db_reader.phone,
                                                     books=reader_books)
            pydantic_readers.append(pydantic_reader)

        file_model = pydantic_models.FileModel(books=books, readers=pydantic_readers)

        logger.debug(f"Saving dump data to file '{filepath}'")
        with open(filepath, "w", encoding="UTF-8") as f:
            f.write(file_model.json(indent=4, ensure_ascii=False))

    @classmethod
    @database.get_database
    def load_from_file(cls, filepath: str, db: database.Session = None):
        """
        Импорт данных в бд из json файла

        :param filepath: Путь до файла
        :param db: Сессия базы данных
        """

        file_model = pydantic_models.FileModel.parse_file(filepath)

        # Заносим книги в базу данных
        for book in file_model.books:
            # Проверяем, есть ли в базе книга с таким кодом
            db_book: database.Book = db.query(database.Book).where(database.Book.code == book.code).first()
            if not db_book:
                # Если книги в бд нет, создаём
                db_book = database.Book(**book.dict())
                db.add(db_book)
            else:
                # Если есть, просто обновляем
                db_book.name = book.name
                db_book.author = book.author
                db_book.count = book.count

        db.commit()

        # Заносим читателей в базу данных
        for reader in file_model.readers:
            db_reader = db.query(database.Reader).where(database.Reader.phone == reader.phone).first()

            if not db_reader:
                db_reader = database.Reader(firstname=reader.firstname,
                                            lastname=reader.lastname,
                                            phone=reader.phone)
                db.add(db_reader)
            else:
                db_reader.firstname = reader.firstname
                db_reader.lastname = reader.lastname
                for assoc in db_reader.books_associations:
                    db.delete(assoc)

            db.commit()

            cls._add_books_to_reader(db_reader, reader.books, db)

    @staticmethod
    def _add_books_to_reader(reader: database.Reader,
                             books: list[pydantic_models.BookIssue],
                             db: database.Session):

        for book_issue in books:
            db_book = db.query(database.Book).where(database.Book.code == book_issue.book_code).first()
            association = database.BookToReader(book_id=db_book.id,
                                                reader_id=reader.id,
                                                issue_date=book_issue.issue_date)

            reader.books_associations.append(association)

        db.commit()
