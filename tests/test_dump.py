from unittest import TestCase
from pathlib import Path
import os

from src.json_dump import Dumper
from src.db import init_db
from src.config_models import ConfigModel
import config

config_model = ConfigModel(**vars(config))
init_db(config_model.database)


class TestDatabase(TestCase):
    def test_file_dump(self):
        test_file_path = "test_dump.json"
        Dumper.dump_to_file(test_file_path)

        is_file_exists = Path(test_file_path).exists()
        self.assertEqual(is_file_exists, True)

        Dumper.load_from_file(test_file_path)

        os.remove(test_file_path)
