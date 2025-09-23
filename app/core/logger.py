from loguru import logger
import sys


# Configure application logger (placeholder)
logger.remove()
logger.add(sys.stderr, format="<green>{time}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

__all__ = ["logger"]
