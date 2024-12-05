# logging_config.py
import logging

def setup_logger():
    """
    Setup logging configuration.
    This function can be called once at the start of the program.
    """
    # You can configure the logging here: e.g., to a file, with a specific level, format, etc.
    logging.basicConfig(
        level=logging.DEBUG,  # Set the root logger to the DEBUG level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler('app.log')  # Also log to file
        ]
    )

