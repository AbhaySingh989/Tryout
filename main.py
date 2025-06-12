# This is the main entry point for the Job Application Agent.

import asyncio # For running async functions like LLM client setup

from job_application_agent import config
from job_application_agent.core_modules import telegram_bot
from job_application_agent.core_modules import error_handler
from job_application_agent.core_modules import llm_interface
from job_application_agent.core_modules import job_manager

# --- Main Application Function ---
async def main():
    """
    Main function to initialize and run the AI Job Application Agent.
    """
    # 1. Setup Logging (This is the very first thing)
    try:
        # Directly use config values. If config.py is missing or keys are absent,
        # the direct attribute access will raise an AttributeError or NameError (if config not imported).
        error_handler.setup_logging(
            log_file_path=config.LOG_FILE_PATH,
            level=config.LOG_LEVEL
        )
    except AttributeError as e:
        # This handles if LOG_FILE_PATH or LOG_LEVEL are missing in a successfully imported config
        import logging
        logging.basicConfig(level=logging.CRITICAL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.critical(f"CRITICAL: Missing essential logging configuration (LOG_FILE_PATH or LOG_LEVEL) in config.py: {e}. Application cannot start properly.", exc_info=True)
        return # Exit main if logging can't be set up
    except NameError as e: # Raised if 'config' itself is not defined (e.g. import failed silently)
        import logging
        logging.basicConfig(level=logging.CRITICAL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.critical(f"CRITICAL: Configuration module 'config' not available. Application cannot start. Error: {e}", exc_info=True)
        return # Exit main
    except Exception as e: # Catch other potential errors during setup_logging itself
        import logging
        # Fallback to basic console logging if file logging setup fails critically
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.critical(f"CRITICAL ERROR setting up file logging: {e}. Logging to console only.", exc_info=True)
        # Depending on desired robustness, could return here if file logging is absolutely essential.
        # For now, allowing it to proceed with console logging if basicConfig in except worked.

    main_logger = error_handler.get_logger(__name__) # Get logger after setup
    main_logger.info("=================================================")
    main_logger.info("AI Job Application Agent - Application Starting")
    main_logger.info("=================================================")
    # Log the actual path and level used by setup_logging, which are from config
    try:
        main_logger.info(f"Logging intended to be configured using file: {config.LOG_FILE_PATH}, level: {config.LOG_LEVEL}")
    except AttributeError:
        main_logger.info("Logging configured (details unavailable due to prior config access issue).")
    except NameError:
        main_logger.info("Logging configured (details unavailable due to prior config module access issue).")


    # 2. Initialize Storage (Job Manager)
    try:
        main_logger.info("Initializing data storage...")
        job_manager.initialize_storage()
        main_logger.info("Data storage initialized successfully.")
    except error_handler.DataStorageError as e:
        main_logger.critical(f"Failed to initialize data storage: {e}. Application cannot proceed.", exc_info=True)
        return # Exit if storage can't be initialized
    except Exception as e:
        main_logger.critical(f"Unexpected error initializing data storage: {e}. Application cannot proceed.", exc_info=True)
        return

    # 3. Configure LLM Client (Gemini)
    try:
        main_logger.info("Configuring LLM client (Gemini)...")
        await llm_interface.configure_genai_client() # This is an async function
        main_logger.info("LLM client configured successfully.")
    except error_handler.ConfigError as e:
        main_logger.critical(f"LLM configuration error: {e}. Bot may not function correctly with LLM features.", exc_info=True)
    except error_handler.LLMInterfaceError as e:
        main_logger.critical(f"Failed to configure LLM client: {e}. Bot may not function correctly with LLM features.", exc_info=True)
    except Exception as e:
        main_logger.critical(f"Unexpected error configuring LLM client: {e}. Bot may not function correctly.", exc_info=True)

    # 4. Start the Telegram Bot
    main_logger.info("Starting Telegram bot...")
    try:
        telegram_bot.run_bot() # This will block until the bot is stopped
    except error_handler.ConfigError as e: # e.g. if Telegram token is missing
        main_logger.critical(f"Telegram bot failed to start due to configuration error: {e}", exc_info=True)
    except Exception as e:
        main_logger.critical(f"Telegram bot crashed with an unexpected error: {e}", exc_info=True)
    finally:
        main_logger.info("===================================================")
        main_logger.info("AI Job Application Agent - Application Shutting Down")
        main_logger.info("===================================================")

# --- Entry Point Guard ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        try:
            # Attempt to get a logger, though logging might not be set up if KI happens very early
            shutdown_logger = error_handler.get_logger(__name__) # Use existing error_handler
            shutdown_logger.info("Application shut down by KeyboardInterrupt (Ctrl+C).")
        except Exception: # If get_logger itself fails or logging isn't setup
            print("Application shut down by KeyboardInterrupt (Ctrl+C). Logging not available or failed.")
    except Exception as e:
        try:
            critical_logger = error_handler.get_logger(__name__)
            critical_logger.critical(f"Application exited due to an unhandled error in main execution: {e}", exc_info=True)
        except Exception:
            print(f"Application exited due to an unhandled error in main execution: {e}. Logging not available or failed.")
