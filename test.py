import logging.config

import config
import style
from src.app import Application
from src.config_models import ConfigModel
from src.style_models import StyleConfig


config_model = ConfigModel(**vars(config))
style_model = StyleConfig(**vars(style))

logging.config.dictConfig(config_model.logging)


if __name__ == "__main__":
    application = Application(config_model, style_model)
    application.mainloop()
