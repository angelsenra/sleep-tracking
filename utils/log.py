#! python3
import logging

FORMAT = ("[%(asctime)s] [\033[92m%(levelname)-8s\033[0m] "
          "\033[94m%(name)-8s\033[0m: %(message)s")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LEVEL = logging.DEBUG


def get(name):
    """
    Get logger with custom name on :const:`LEVEL`
    using :const:`FORMAT` and :const:`DATE_FORMAT`

    :param str name: Name of the logger object
    :returns: The logger object
    """
    logger = logging.getLogger(name)
    logger.setLevel(LEVEL)

    fh = logging.StreamHandler()
    fh.setLevel(LEVEL)
    fh.setFormatter(logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT))

    logger.addHandler(fh)

    return logger
