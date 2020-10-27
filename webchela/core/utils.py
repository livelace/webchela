import coloredlogs
import logging
import psutil
import sys

from random import randint

from webchela.core.vars import *

logger = logging.getLogger("webchela.utils")
coloredlogs.install(fmt=DEFAULT_LOG_FORMAT, level=DEFAULT_LOG_LEVEL)


def exit_handler(sig, frame):
    logger.info("Exit.")
    sys.exit(0)


def gen_hash():
    s = "abcdefghijklmnopqrstuvwxyz1234567890"
    h = [s[randint(0, len(s) - 1)] for _ in range(0, 5)]

    return "".join(h)


def get_load(cpu, mem, interval=1):
    # get base metrics.
    cpu_load = int(psutil.cpu_percent(interval=interval))
    mem_free = int(psutil.virtual_memory().available)

    # calculate load score.
    cpu_cores = psutil.cpu_count()
    cpu_freq_max = int(psutil.cpu_freq().max)
    if cpu_freq_max != 0:
        cpu_freq = cpu_freq_max
    else:
        cpu_freq = 2600  # virtual cpus don't provide max frequency value, use static value.

    cpu_score = cpu_cores * cpu_freq / cpu_load
    score = int(cpu_score * mem_free / 1024 / 1024 / 1024)

    if cpu_load <= cpu and mem_free >= mem:
        return True, cpu_load, mem_free, score
    else:
        return False, cpu_load, mem_free, score


def human_size(size):
    for x in ['B', 'K', 'M', 'G', 'T']:
        if size < 1024.0:
            return "%d%s" % (size, x)
        size /= 1024.0

    return size


def split_urls(urls, amount):
    urls_parts = [urls[i:i + amount] for i in range(0, len(urls), amount)]

    return urls_parts
