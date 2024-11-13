import logging
import sys

loglevel = 'info'
errorlog = '-'
accesslog = '-'
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}

if __name__ != '__main__':
    # Adjust the loggers for the workers.
    loggers = logging.root.manager.loggerDict
    for logger_name in loggers:
        if 'gunicorn' in logger_name:
            loggers[logger_name].setLevel(logging.INFO)
            loggers[logger_name].addHandler(logging.StreamHandler(sys.stdout))
