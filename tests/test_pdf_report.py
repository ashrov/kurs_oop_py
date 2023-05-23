from unittest import TestCase
from pathlib import Path
import os

from src.pdf_report import create_pdf_report
from src.db import init_db
from src.config_models import ConfigModel
import config

config_model = ConfigModel(**vars(config))
init_db(config_model.database)


class TestPdf(TestCase):
    def test_pdf_report(self):
        test_file_path = "test_pdf_report.pdf"
        create_pdf_report(test_file_path)

        is_file_exists = Path(test_file_path).exists()
        self.assertEqual(is_file_exists, True)
        os.remove(test_file_path)
