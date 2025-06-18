# This is the main entry point for the Job Application Agent.

import asyncio # For running async functions like LLM client setup

from job_application_agent import config
# Updated telegram_bot imports
from job_application_agent.core_modules.telegram_bot import (
    setup_bot,
    start_bot_async,
    shutdown_bot_async
)
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
        llm_interface.configure_genai_client() # This is an async function
        main_logger.info("LLM client configured successfully.")
    except error_handler.ConfigError as e:
        main_logger.critical(f"LLM configuration error: {e}. Bot may not function correctly with LLM features.", exc_info=True)
    except error_handler.LLMInterfaceError as e:
        main_logger.critical(f"Failed to configure LLM client: {e}. Bot may not function correctly with LLM features.", exc_info=True)
    except Exception as e:
        main_logger.critical(f"Unexpected error configuring LLM client: {e}. Bot may not function correctly.", exc_info=True)

    # 4. Setup and Start the Telegram Bot
    application = None # Ensure application is defined for the finally block
    try:
        main_logger.info("Setting up Telegram bot...")
        # setup_bot() can raise ConfigError if token is missing or other setup issues.
        application = setup_bot()
        # If setup_bot raises an error, it will be caught by the ConfigError or generic Exception handlers below.

        main_logger.info("Starting Telegram bot polling...")
        await start_bot_async(application) # Start polling
        main_logger.info("Telegram bot polling started. Bot is running.")

        # Keep the main task alive indefinitely until a shutdown signal (e.g., KeyboardInterrupt)
        # This allows the bot's background threads (for polling) to continue running.
        while True:
            await asyncio.sleep(3600) # Sleep for a long time (e.g., 1 hour)
            # This loop will be broken by KeyboardInterrupt or if the bot stops for other critical reasons.

    except error_handler.ConfigError as e: # Catches ConfigError from setup_bot or other config issues
        main_logger.critical(f"Telegram bot setup or startup failed due to configuration error: {e}", exc_info=True)
    except error_handler.TelegramBotError as e: # Catches specific bot errors from start_bot_async
        main_logger.critical(f"Telegram bot failed during startup or runtime: {e}", exc_info=True)
    except Exception as e: # Catch any other unexpected errors during bot setup/startup
        main_logger.critical(f"Telegram bot crashed with an unexpected error during setup/startup: {e}", exc_info=True)
    finally:
        main_logger.info("Attempting to shut down Telegram bot gracefully...")
        if application: # Check if application was successfully initialized
            await shutdown_bot_async(application)
            main_logger.info("Telegram bot shut down.")
        else:
            main_logger.info("Telegram bot application was not initialized; no specific bot shutdown needed.")

        main_logger.info("===================================================")
        main_logger.info("AI Job Application Agent - Application Shutting Down")
        main_logger.info("===================================================")

# --- Entry Point Guard ---
if __name__ == "__main__":
    # The main() function is now fully async and handles its own lifecycle.
    # KeyboardInterrupt is caught inside asyncio.run() or by the finally block in main().
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This outer KeyboardInterrupt catch is primarily for the case where asyncio.run(main())
        # itself is interrupted before main's own try/except/finally can fully handle it,
        # or if an interrupt occurs during the final logging in main's finally block.
        # Most graceful shutdown logic (including bot shutdown) should be within main()'s finally.
        try:
            # Try to get a logger; it might fail if logging wasn't set up or was torn down.
            shutdown_logger = error_handler.get_logger(__name__)
            shutdown_logger.info("Application shut down by KeyboardInterrupt (Ctrl+C) at entry point.")
        except Exception:
            print("Application shut down by KeyboardInterrupt (Ctrl+C) at entry point. Logging not available.")
    except Exception as e: # Catch any other completely unhandled exceptions from asyncio.run(main())
        try:
            critical_logger = error_handler.get_logger(__name__)
            critical_logger.critical(f"Application exited due to a critical unhandled error at entry point: {e}", exc_info=True)
        except Exception:
            print(f"Application exited due to a critical unhandled error at entry point: {e}. Logging not available.")