import logging.config
import logging
import os
from path import bot_logs_path

try:
    if os.path.exists(bot_logs_path):
        pass
    else:
        os.mkdir(bot_logs_path)
    path_logs = os.path.join(bot_logs_path, 'log.log')
    open(path_logs, 'a').close()
except Exception as _ex:
    logging.critical(f'Error opening json: {_ex}')

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default_formatter': {
            'format': '[%(levelname)s:%(asctime)s][%(name)s][%(lineno)d] %(message)s'
        },
    },

    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
            'level': 'DEBUG'
        },
        'rotating_files_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default_formatter',
            'filename': path_logs,
            'encoding': 'UTF-8',
            'maxBytes': 1000000,
            'backupCount': 3,
            'level': 'INFO',
            'mode': 'a'
        },
    },

    'loggers': {
        'BOT': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'DATABASE': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'USER_HANDLERS': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'ADMIN_HANDLERS': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'EMPLOYEE_HANDLERS': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'SERVER_HANDLERS': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'IIKO_API': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'IIKO_CLOUD_API': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
        'GEO_API': {
            'handlers': ['stream_handler', 'rotating_files_handler'],
            'propagate': True,
            'level': 'DEBUG'
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

bot_logger = logging.getLogger('BOT')
database_logger = logging.getLogger('DATABASE')
user_handlers_logger = logging.getLogger('USER_HANDLERS')
admin_handlers_logger = logging.getLogger('ADMIN_HANDLERS')
employee_handlers_logger = logging.getLogger('EMPLOYEE_HANDLERS')
server_logger = logging.getLogger('SERVER_HANDLERS')
iiko_api_logger = logging.getLogger('IIKO_API')
iiko_cloud_api_logger = logging.getLogger('IIKO_CLOUD_API')
geo_api_logger = logging.getLogger('GEO_API')
