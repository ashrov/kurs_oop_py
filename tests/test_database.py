from unittest import TestCase

from src.db import init_db, wrap_with_database, Session, Book
from src.config_models import ConfigModel
import config

config_model = ConfigModel(**vars(config))
init_db(config_model.database)


class TestDatabase(TestCase):
    @wrap_with_database
    def test_database(self, db: Session = None):
        test_book = Book(code="test_code_123",
                         name="test_name_123",
                         author="test_author_123",
                         count=12345)

        db.add(test_book)
        db.commit()

        book = db.query(Book).where(Book.code == "test_code_123").first()
        self.assertNotEqual(book, None)
        self.assertEqual(book.name, "test_name_123")

        db.delete(book)
        db.commit()
