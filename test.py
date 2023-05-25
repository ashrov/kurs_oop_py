import logging

import config
from src.db import init_db
from src.app import Application
from src.config_models import ConfigModel


logging.basicConfig(level=logging.DEBUG)


config_model = ConfigModel(**vars(config))


if __name__ == "__main__":
    application = Application(config_model)
    application.mainloop()
