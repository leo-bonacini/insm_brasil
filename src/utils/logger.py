"""Logging configuration using loguru."""
import sys
from loguru import logger
from src.utils.config import ROOT

LOG_PATH = ROOT / "logs"
LOG_PATH.mkdir(exist_ok=True)


def setup_logger(level: str = "INFO") -> None:
    logger.remove()
    logger.add(sys.stdout, level=level, colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.add(LOG_PATH / "pipeline_{time:YYYY-MM-DD}.log", rotation="10 MB", retention="30 days", level="DEBUG")


setup_logger()
