import logging


def bot_logger() -> logging.Logger:
    log_file_path = 'logging_exception.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)

    file_handler = logging.FileHandler(log_file_path)
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
