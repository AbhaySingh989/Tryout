# This is the main entry point for the Job Application Agent.

import asyncio # For running async functions like LLM client setup

# Explicitly import config from the job_application_agent package,
# assuming config.py resides within the job_application_agent directory.
# This was the outcome of step 7.1.
try:
    from job_application_agent import config
except ModuleNotFoundError:
    # This might happen if main.py is run in a way that job_application_agent is not in PYTHONPATH.
    # Or if config.py is indeed in the root. For this project, it's intended to be in job_application_agent/.
    print("CRITICAL: Could not import 'config' from 'job_application_agent'. Ensure config.py is in the 'job_application_agent' directory and the parent directory is in PYTHONPATH if running from outside the project root.")
    # Attempt a direct import as a last resort, which might work if config.py is in the same dir as main.py (root)
    # AND main.py is run from the root.
    try:
        import config # type: ignore
        print("INFO: Successfully imported 'config' directly. This implies config.py might be in the root directory.")
    except ImportError:
        print("CRITICAL: Failed both ways of importing 'config'. Application cannot reliably start.")
        # A simple config object could be created here with defaults if absolutely necessary for basic logging,
        # but it's better to fix the import. For now, exit or let it fail later.
        # For the purpose of this script, we'll let it proceed and potentially fail if config attributes are needed.
        pass


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
    log_file_path_to_use = "job_application_agent/logs/app_default.log" # Default fallback
    log_level_to_use = "INFO" # Default fallback

    try:
        # Check if 'config' module was successfully imported and has the attributes
        if 'config' in globals() and hasattr(config, 'LOG_FILE_PATH') and hasattr(config, 'LOG_LEVEL'):
            log_file_path_to_use = config.LOG_FILE_PATH
            log_level_to_use = config.LOG_LEVEL
        else:
            # If config not loaded, this warning goes to console via basicConfig in error_handler's except block
            print("WARNING: 'config' module or its logging attributes (LOG_FILE_PATH, LOG_LEVEL) not found. Using default logging settings.")

        error_handler.setup_logging(log_file_path=log_file_path_to_use, level=log_level_to_use)

    except Exception as e: # Catch other potential errors during setup_logging
        # Fallback to basic console logging if file logging setup fails critically
        import logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.critical(f"CRITICAL ERROR setting up file logging: {e}. Logging to console only.", exc_info=True)

    main_logger = error_handler.get_logger(__name__) # Get logger after setup
    main_logger.info("=================================================")
    main_logger.info("AI Job Application Agent - Application Starting")
    main_logger.info("=================================================")

    # Log config loading status
    if 'config' not in globals() or not hasattr(config, 'LOG_FILE_PATH'):
        main_logger.warning("Logging was set up with default values because 'config' module or its attributes were not available at the time of logging setup.")
    else:
        main_logger.info(f"Logging configured to use file: {log_file_path_to_use}, level: {log_level_to_use}")


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
