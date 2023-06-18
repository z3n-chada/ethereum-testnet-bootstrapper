"""
    Various utility functions that are used throughout common applications.
"""
import logging

logging_levels: dict = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def get_logger(log_level: str, name: str,
               format_str: str = "%(asctime)s [%(levelname)s] %(message)s") -> logging.Logger:
    """
    Returns a logger with the given log level and name.
    @param log_level: The log level to use.
    @param name: The name of the logger.
    @param format_str: The format of the logger (default: "%(asctime)s %(levelname)s %(message)s").
    @return: The logger.
    """

    if log_level not in logging_levels:
        raise Exception(f"Unknown log level: {log_level}")
    logging.basicConfig(format=format_str)
    logger = logging.getLogger(name)
    logger.setLevel(logging_levels[log_level])
    return logger
