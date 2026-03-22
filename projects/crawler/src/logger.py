# -*- coding: utf-8 -*-
"""
Logging Configuration for Crawler
"""
import logging
import sys
from typing import Optional


def setup_logger(name: str = 'crawler', verbose: bool = False) -> logging.Logger:
    """
    Setup logger with configurable level.
    
    Args:
        name: Logger name
        verbose: If True, use DEBUG level; otherwise INFO level
    
    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


# Default logger instance
default_logger = setup_logger()


# Convenience functions
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger by name, or return default logger"""
    if name:
        return logging.getLogger(f'crawler.{name}')
    return default_logger


def set_verbose(verbose: bool = True):
    """Set verbose mode for default logger"""
    level = logging.DEBUG if verbose else logging.INFO
    default_logger.setLevel(level)
    for handler in default_logger.handlers:
        handler.setLevel(level)


__all__ = [
    'setup_logger',
    'get_logger',
    'set_verbose',
    'default_logger',
]
