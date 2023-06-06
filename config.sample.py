database = {
    "host": "localhost",
    "port": "3306",
    "user": "library_user",
    "password": "",
    "database": ""
}

logging = {
    "version": 1,

    "formatters": {
        "default": {
            "format": "%(asctime)s:%(filename)s:%(filename)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },

    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
            "formatter": "default"
        }
    },

    "loggers": {
        "src": {
            "handlers": ["stdout"],
            "level": "DEBUG",
            "propagate": "true"
        }
    }
}
