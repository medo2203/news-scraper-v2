import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

def setup_logger(script_name: str = 'news_scraper'):
    """
    Creates a log directory if it doesn't exist daily to store logs for all python scripts.
    Logs are written both to a rotating file and the console.

    Parameters:
        script_name (str): The name of the script for which the logger is being set up.

    Returns:
        logger (logging.Logger): Configured logger instance.
    """
    log_dir = "./log"
    os.makedirs(log_dir, exist_ok=True)

    # Log file name with current date
    current_date = datetime.now().strftime("%d-%m-%Y")
    log_file = os.path.join(log_dir, f"{current_date}.log")
    
    # Set up the logger
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if the logger is reused
    if not logger.handlers:

        # File handler with daily rotation
        file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
