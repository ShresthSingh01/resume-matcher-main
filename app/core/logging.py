import sys
from loguru import logger
import json
import logging

class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    Intercepts standard logging messages and redirects them to loguru.
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    # Remove default logger
    logger.remove()

    # Determine environment (default to dev for now, can be env var driven)
    # For production, we want JSON logs
    # logger.add(sys.stdout, serialize=True, level="INFO")
    
    # For Dev, keep it readable
    logger.add(
        sys.stdout, 
        colorize=True, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File rotation
    logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="DEBUG")

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    
    return logger
