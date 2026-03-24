import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    logger.remove()
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    logger.add(
        "/app/data/prepai.log",
        level="INFO",
        rotation="1 week",
        retention="1 month",
        compression="gz",
    )
    return logger
