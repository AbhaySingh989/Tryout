import logging
import os

# --- Custom Exception Classes ---
class JobApplicationAgentError(Exception):
    """Base class for custom exceptions in the Job Application Agent."""
    pass

class CVParserError(JobApplicationAgentError):
    """Custom exception for errors during CV parsing."""
    pass

class LLMInterfaceError(JobApplicationAgentError):
    """Custom exception for errors interacting with the LLM."""
    pass

class WebScraperError(JobApplicationAgentError):
    """Custom exception for errors during web scraping."""
    pass

class TelegramBotError(JobApplicationAgentError):
    """Custom exception for errors related to the Telegram bot."""
    pass

class ConfigError(JobApplicationAgentError):
    """Custom exception for configuration errors."""
    pass

class DataStorageError(JobApplicationAgentError):
    """Custom exception for data storage errors."""
    pass

# --- Logging Setup ---
_root_logger_configured = False

def setup_logging(log_file_path: str, level: str = "INFO"):
    """
    Configures basic file and console logging for the application.

    This function should ideally be called once at the application startup.
    It configures the root logger. Subsequent calls to logging.getLogger()
    will retrieve loggers that inherit this configuration.

    Args:
        log_file_path (str): The full path to the log file.
        level (str): The logging level (e.g., 'DEBUG', 'INFO', 'WARNING').
    """
    global _root_logger_configured
    if _root_logger_configured:
        logging.getLogger(__name__).warning("setup_logging called multiple times. Logging already configured.")
        return

    log_level_int = getattr(logging, level.upper(), logging.INFO)

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file_path)
    if log_dir: # Check if log_dir is not an empty string (e.g. if log_file_path is just "app.log")
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                logging.info(f"Log directory created: {log_dir}")
        except OSError as e:
            # Fallback to basic console logging for this specific error
            logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
            logging.error(f"CRITICAL: Failed to create log directory {log_dir}: {e}. File logging may fail.")
            # Depending on desired robustness, could raise here or just log.
            # For now, we'll let it proceed, and logging to file might fail,
            # but at least this specific error is noted.

    # Configure root logger
    # Using basicConfig is fine for simpler setups. For more control (e.g. multiple handlers with different
    # levels or formatters), you would get the root logger and add handlers to it manually.
    logging.basicConfig(
        level=log_level_int,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, mode='a'), # 'a' for append
            logging.StreamHandler()  # Log to console (stderr by default)
        ],
        # force=True # Use with caution: force=True can be useful if re-configuring, but ensure it's intended.
                   # Not using it here to avoid masking multiple calls if setup_logging is called incorrectly.
    )

    _root_logger_configured = True
    # Get a logger for this module to log the successful setup.
    # This logger will now use the configuration set by basicConfig.
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured. Level: {level.upper()}. File: {log_file_path}")


def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance.
    It's a simple wrapper around logging.getLogger(name).
    Assumes setup_logging() has been called at application startup.

    Args:
        name (str): The name for the logger (typically __name__ of the calling module).

    Returns:
        logging.Logger: Logger instance.
    """
    if not _root_logger_configured:
        # This is a safeguard. Ideally, setup_logging is called once in main.py.
        # If not, loggers obtained before setup_logging will use default settings.
        # We could raise an error here, or log a warning.
        # For now, we'll log a warning to the default logger.
        # This warning might not go to the file if setup_logging is called later.
        logging.warning(
            f"get_logger('{name}') called before global logging setup. "
            "Logging may not be fully configured yet. Call setup_logging() early in your application."
        )
    return logging.getLogger(name)

if __name__ == '__main__':
    # This block is for testing the error_handler module directly.
    # In the actual application, setup_logging would be called from main.py,
    # using configuration values from config.py.

    # --- Mocking config values for standalone testing ---
    # Construct a path relative to the script's location if possible, or use an absolute path.
    # For this example, let's assume the script is run from the project root or similar context.
    # If job_application_agent/core_modules/error_handler.py is run directly,
    # 'job_application_agent/logs/' might be relative to where you run it.
    # For robustness in testing, it's better to define an absolute path or a path relative to this file.

    # Assuming this script is in job_application_agent/core_modules/
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_approx = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
    MOCK_LOG_FILE_PATH = os.path.join(project_root_approx, "job_application_agent", "logs", "error_handler_test.log")
    MOCK_LOG_LEVEL = "DEBUG"

    print(f"--- error_handler.py standalone test ---")
    print(f"Attempting to set up logging.")
    print(f"Log file path for test: {MOCK_LOG_FILE_PATH}")
    print(f"Log level for test: {MOCK_LOG_LEVEL}")

    # Ensure the test log directory exists for the test log file
    test_log_dir = os.path.dirname(MOCK_LOG_FILE_PATH)
    if not os.path.exists(test_log_dir):
        try:
            os.makedirs(test_log_dir)
            print(f"Test log directory created: {test_log_dir}")
        except OSError as e:
            print(f"Error creating test log directory {test_log_dir}: {e}")
            # If directory creation fails, the test might not log to file as expected.

    setup_logging(log_file_path=MOCK_LOG_FILE_PATH, level=MOCK_LOG_LEVEL)

    # Test getting a logger after setup
    module_logger = get_logger(__name__) # __name__ will be '__main__' here

    module_logger.debug("This is a debug message from error_handler standalone test.")
    module_logger.info("This is an info message from error_handler standalone test.")
    module_logger.warning("This is a warning message from error_handler standalone test.")

    try:
        raise CVParserError("Failed to parse the CV during test.")
    except CVParserError as e:
        module_logger.error(f"Caught a CVParserError (expected): {e}", exc_info=True) # Log with stack trace

    try:
        raise LLMInterfaceError("LLM API returned an error during test.")
    except LLMInterfaceError as e:
        module_logger.exception(f"Caught an LLMInterfaceError (expected)") # logger.exception also includes stack trace

    try:
        1 / 0
    except ZeroDivisionError as e:
        module_logger.error(f"Caught a ZeroDivisionError (expected): {e}", exc_info=True)

    module_logger.info("Simulating a call to get_logger before setup (for testing the warning).")
    _root_logger_configured = False # Temporarily reset for test
    logger_before_setup = get_logger("test_before_setup")
    logger_before_setup.warning("This warning is from a logger obtained before (simulated) setup_logging.")
    # Re-configure for any subsequent tests if needed, or end here.
    # setup_logging(log_file_path=MOCK_LOG_FILE_PATH, level=MOCK_LOG_LEVEL) # Re-initialize if more tests follow

    print(f"--- Standalone test complete. Check the log file: {MOCK_LOG_FILE_PATH} ---")
    print(f"--- Also check console output for logs. ---")
