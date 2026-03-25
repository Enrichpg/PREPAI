import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    logger.remove()
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    
    # Always log to stdout
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # Try to log to file if data path is writable
    try:
        log_file = f"{settings.DATA_PATH}/prepai.log"
        logger.add(
            log_file,
            level="INFO",
            rotation="1 week",
            retention="1 month",
            compression="gz",
        )
    except (PermissionError, OSError):
        # Fallback for local development/tests where /app/data doesn't exist
        pass

    return logger
