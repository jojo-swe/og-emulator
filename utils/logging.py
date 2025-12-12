"""Logging utilities for the emulator."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Union

def setup_logging(
    level: Union[str, int] = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> None:
    """Set up logging for the emulator.
    
    Args:
        level: Logging level (name or numeric value)
        log_file: Log file path (if None, logs to console only)
        console: Whether to log to console
    """
    # Convert string level to numeric
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Add file handler if requested
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        os.makedirs(log_path.parent, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
