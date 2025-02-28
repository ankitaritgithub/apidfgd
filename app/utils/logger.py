# logger.py
import logging
import os

# Get the directory two levels above the current working directory
log_dir = os.getcwd()

# Define the full log file path
log_file_path = os.path.join(log_dir, 'app.log')

# Configure the logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Customize the log format
    handlers=[
        logging.FileHandler(log_file_path),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)

# Create a logger instance
# You can use this logger in other files by importing it
logger = logging.getLogger(__name__)


