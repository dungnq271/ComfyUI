import logging
import logging.config
from pathlib import Path

import coloredlogs
import yaml  # type: ignore


def setup_coloredlogs(name: str, level: str = "INFO"):
    coloredlogs.install(
        level=level, fmt="%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"
    )
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(name)
    return logger


def get_logger(name):
    return logging.getLogger(name)
