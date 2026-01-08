"""
Structured Logging Configuration
================================
Centralized logging for schedule-parse project
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file with date
LOG_FILE = LOG_DIR / f"schedule_parser_{datetime.now().strftime('%Y%m%d')}.log"


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__ from calling module)

    Returns:
        Configured logger instance

    Usage:
        from core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Message here")
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_format)

        # File handler (DEBUG and above)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# Convenience function for quick debug logging
def log_ocr_result(text_lines: list, carrier: str = None, confidence: float = None):
    """Log OCR extraction results for debugging"""
    logger = get_logger("ocr")
    logger.debug(f"OCR Result - Carrier: {carrier}, Lines: {len(text_lines)}, Confidence: {confidence}")
    if text_lines:
        logger.debug(f"First 3 lines: {text_lines[:3]}")


def log_parse_result(schedules: list, carrier: str, source_file: str = None):
    """Log parsing results"""
    logger = get_logger("parser")
    logger.info(f"Parsed {len(schedules)} schedules from {carrier}")
    if source_file:
        logger.debug(f"Source: {source_file}")
    for s in schedules[:3]:  # Log first 3
        logger.debug(f"  - {s.vessel} / {s.voyage} | ETD: {s.etd} | ETA: {s.eta}")


def log_vessel_match(ocr_text: str, matched: str, confidence: int, match_type: str):
    """Log vessel matching results"""
    logger = get_logger("vessel_db")
    if match_type == "exact":
        logger.debug(f"Vessel exact match: '{ocr_text}' -> '{matched}'")
    elif match_type == "fuzzy":
        logger.info(f"Vessel fuzzy match: '{ocr_text}' -> '{matched}' ({confidence}%)")
    else:
        logger.warning(f"Vessel no match: '{ocr_text}'")
