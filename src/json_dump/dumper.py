from logging import getLogger

from . import pydantic_models
from .. import db as database


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
            reader_books = [reader_book.code for reader_book in db_reader.books]
            pydantic_reader = pydantic_models.Reader(firstname=db_reader.firstname,
                                                     lastname=db_reader.lastname,
                                                     phone=db_reader.phone,
                                                     books=reader_books)
            pydantic_readers.append(pydantic_reader)

        file_model = pydantic_models.FileModel(books=books, readers=pydantic_readers)

        logger.debug(f"Saving dump data to file '{filepath}'")
        with open(filepath, "w") as f:
            f.write(file_model.json(indent=4, ensure_ascii=False))

    @staticmethod
    @database.get_database
    def load_from_file(filepath: str, db: database.Session = None):
        """
        Импорт данных в бд из json файла

        :param filepath: Путь до файла
        :param db: Сессия базы данных
        """

        file_model = pydantic_models.FileModel.parse_file(filepath)

        for book in file_model.books:
            db_book: database.Book = db.query(database.Book).where(database.Book.code == book.code).first()
            if not db_book:
                db_book = database.Book(**book.dict())
                db.add(db_book)
            else:
                db_book.name = book.name
                db_book.author = book.author
                db_book.count = book.count

        db.commit()

        for reader in file_model.readers:
            db_reader: database.Reader = db.query(database.Reader).where(database.Reader.phone == reader.phone).first()
            db_books = [db.query(database.Book).where(database.Book.code == book_code).first()
                        for book_code in reader.books]

            if not db_reader:
                db_reader = database.Reader(**reader.dict())
                db.add(db_reader)
            else:
                db_reader.firstname = reader.firstname
                db_reader.lastname = reader.lastname
            db_reader.books = db_books

        db.commit()
