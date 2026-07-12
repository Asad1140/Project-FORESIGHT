# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Utility and Formatter Functions
--------------------------------------------------
Contains general helpers, mathematical formatters, and central logging setup.
"""

from pathlib import Path
import logging
from config import APP_LOG_FILE


def format_rupees(val: float) -> str:
    """
    Formats raw numeric rupee values into readable string representations.
    Renders values >= 100,000 in Lakhs (L) and smaller values with thousands comma.

    Args:
        val (float): Raw currency value in Rupees.

    Returns:
        str: Formatted currency string.
    """
    if val >= 100000:
        return f"₹{val/100000:.2f}L"
    return f"₹{val:,.0f}"


def setup_logging() -> logging.Logger:
    """
    Configures and retrieves the application root logger. Ensures both
    console stream and file handlers (writing to logs/app.log) are attached
    to record all module-level logger messages.

    Returns:
        logging.Logger: The configured root Logger instance.
    """
    logger = logging.getLogger()  # Root logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    # Check existing handlers specifically for our log file
    has_file = False
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            try:
                if Path(handler.baseFilename).resolve() == Path(APP_LOG_FILE).resolve():
                    has_file = True
                    break
            except Exception:
                pass
            
    # Add file handler if not already present
    if not has_file:
        Path(APP_LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    # Ensure there is at least one stream handler
    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
    return logger
