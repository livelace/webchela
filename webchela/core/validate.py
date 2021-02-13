import coloredlogs
import logging
import os
import re

from webchela.core.utils import human_size
from webchela.core.vars import *

logger = logging.getLogger("webchela.validate")
coloredlogs.install(fmt=DEFAULT_LOG_FORMAT, level=DEFAULT_LOG_LEVEL)


def is_bool(name, value, default):
    if isinstance(value, bool):
        v = value
    else:
        v = default

    logger.debug("{}: {}".format(name, v))
    return v


def is_browser_geometry(name, value, default):
    vl = str(value).lower()

    if re.match("^[0-9]+x[0-9]+$", vl):
        x, y = vl.split("x")
        v = value
    else:
        x, y = default.split("x")
        v = default

    if name:
        logger.debug("{}: {}".format(name, v))

    return v, int(x), int(y)


def is_browser_type(name, value, default):
    vl = str(value).lower()
    if vl == "chrome" or vl == "firefox":
        v = vl
    else:
        v = default

    if name:
        logger.debug("{}: {}".format(name, v))

    return v


def is_bytes(name, value, default):
    vu = str(value).upper()
    v = ""

    if re.match("^[0-9]+[BKMG]", vu):
        if vu.endswith('B'):
            v = int(vu[:-1])

        elif vu.endswith('K'):
            v = int(vu[:-1]) * 1024

        elif vu.endswith('M'):
            v = int(vu[:-1]) * 1024 * 1024

        elif vu.endswith('G'):
            v = int(vu[:-1]) * 1024 * 1024 * 1024

    elif isinstance(value, int):
        v = value

    else:
        v = default

    logger.debug("{}: {}".format(name, human_size(v)))
    return v


def is_dir(name, value, default):
    if os.path.isdir(value):
        v = value
    else:
        try:
            os.makedirs(value)
            v = value
        except:
            v = default

    logger.debug("{}: {}".format(name, v))
    return v


def is_file(name, value, default):
    if os.path.isfile(value):
        v = value
    else:
        v = default

    logger.debug("{}: {}".format(name, v))
    return v


def is_int(name, value, default):
    if isinstance(value, int):
        v = value
    else:
        v = default

    logger.debug("{}: {}".format(name, v))
    return v


def is_list(name, value, default):
    if isinstance(value, list):
        v = value
    else:
        v = default

    logger.debug("{}: {}".format(name, v))
    return v


def is_log_level(value, default):
    v = str(value).upper()
    levels = ["SPAM", "DEBUG", "VERBOSE", "INFO", "NOTICE", "WARNING", "SUCCESS", "ERROR", "CRITICAL"]
    if v in levels:
        return v
    else:
        return default


def is_string(name, value, default):
    if isinstance(value, str):
        v = value
    else:
        v = default

    logger.debug("{}: {}".format(name, v))
    return v

