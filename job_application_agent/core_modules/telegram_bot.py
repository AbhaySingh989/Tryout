import io
import os
import json # For storing user data if needed, and for LLM interactions

from telegram import Update, File as TelegramFile # Renamed to avoid conflict
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

from job_application_agent import config
from job_application_agent.core_modules.error_handler import (
    get_logger,
    TelegramBotError,
    CVParserError,
    LLMInterfaceError,
    ConfigError
)
# LLM Interface functions are async
from job_application_agent.core_modules.llm_interface import (
    configure_genai_client as configure_llm_client, # Renamed for clarity
    analyze_cv_text,
    generate_clarification_questions,
    # For future use: generate_cover_letter_snippet, check_job_fit
)
from job_application_agent.core_modules.cv_parser import parse_cv
# from job_application_agent.core_modules.job_manager import store_user_preferences # Placeholder

logger = get_logger(__name__)

# --- Conversation States ---
ASK_CV, HANDLE_CV, ASK_QUESTIONS, HANDLE_ANSWERS = range(4)

# --- Utility Functions ---
async def ensure_llm_client_configured():
    """Ensures the LLM client is configured."""
    # This is a simplified check. In a real app, configure_llm_client()
    # should be called once at startup.
    try:
        # Accessing a global or a stateful check in llm_interface if it exists,
        # or just calling it (it should be idempotent).
        await configure_llm_client()
    except ConfigError as e:
        logger.error(f"LLM Client Configuration failed: {e}")
        raise # Re-raise to be handled by the calling function

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the CV."""
    user = update.message.from_user
    logger.info(f"User {user.id} ({user.username}) started conversation with /start.")
    await update.message.reply_text(
        "Welcome to the AI Job Application Agent! \n\n"
        "I can help you find and apply for jobs. To begin, please upload your CV "
        "(PDF or DOCX format). \n\n"
        "You can send /cancel at any time to stop our current conversation."
    )
    return ASK_CV

async def handle_cv_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles CV upload, parses it, and asks the first clarification question."""
    user = update.message.from_user
    message = update.message

    if not message.document:
        await message.reply_text("Hmm, that doesn't look like a file. Please upload your CV as a PDF or DOCX document.")
        return ASK_CV

    doc = message.document
    file_name = doc.file_name

    # Basic check for file extension (more robust checks in cv_parser)
    if not (file_name.lower().endswith(".pdf") or file_name.lower().endswith(".docx")):
        logger.warning(f"User {user.id} uploaded unsupported file type: {file_name}")
        await message.reply_text(
            "Unsupported file type. Please upload your CV in PDF or DOCX format."
        )
        return ASK_CV

    logger.info(f"User {user.id} uploaded CV: {file_name} (Size: {doc.file_size} bytes)")
    await message.reply_text(f"Received your CV: {file_name}. Processing it now...")

    try:
        await ensure_llm_client_configured() # Ensure LLM client is ready

        cv_file: TelegramFile = await doc.get_file()
        cv_file_stream = io.BytesIO()
        await cv_file.download_to_memory(cv_file_stream)
        cv_file_stream.seek(0) # Reset stream position to the beginning

        logger.debug(f"CV for user {user.id} downloaded to memory. Size: {cv_file_stream.getbuffer().nbytes}")

        # 1. Parse CV
        raw_cv_text = parse_cv(cv_file_stream, file_name)
        if not raw_cv_text:
            logger.warning(f"CV parsing for {file_name} (user {user.id}) resulted in empty text.")
            await message.reply_text(
                "I couldn't extract any text from your CV. It might be an image-based file or corrupted. "
                "Please try a different CV file."
            )
            return ASK_CV

        logger.info(f"CV for user {user.id} parsed successfully. Raw text length: {len(raw_cv_text)}")
        context.user_data['raw_cv_text'] = raw_cv_text # Store for potential later use

        # 2. Analyze CV with LLM
        await message.reply_text("Analyzing your CV with AI to understand your skills and experience...")
        cv_analysis = await analyze_cv_text(raw_cv_text)
        context.user_data['cv_analysis'] = cv_analysis
        logger.info(f"CV for user {user.id} analyzed by LLM. Analysis keys: {list(cv_analysis.keys())}")

        # 3. Generate Clarification Questions
        await message.reply_text("Generating a few questions to tailor your job search...")
        questions = await generate_clarification_questions(cv_analysis)
        if not questions:
            logger.warning(f"LLM generated no clarification questions for user {user.id}.")
            await message.reply_text(
                "I have analyzed your CV. For now, I don't have any further questions. "
                "We can proceed with job searching based on this. (This part is under development)"
            )
            # Here, you might transition to a job search state or end.
            # For now, ending conversation as question handling is the next step.
            # Simulate storing preferences
            # store_user_preferences(user.id, {"cv_analysis": cv_analysis, "preferences_via_questions": {}})
            logger.info(f"User {user.id} preferences (CV only) stored.")
            return ConversationHandler.END

        context.user_data['questions'] = questions
        context.user_data['answers'] = {}
        context.user_data['current_question_index'] = 0

        logger.info(f"Generated {len(questions)} questions for user {user.id}.")
        await message.reply_text("Great! Let's clarify a few things to personalize your job search.")
        await message.reply_text(questions[0])
        return ASK_QUESTIONS

    except CVParserError as e:
        logger.error(f"CVParserError for user {user.id} with file {file_name}: {e}", exc_info=True)
        await message.reply_text(f"Error parsing your CV: {e}. Please try a different file or ensure it's not corrupted.")
        return ASK_CV
    except LLMInterfaceError as e:
        logger.error(f"LLMInterfaceError for user {user.id} while processing CV {file_name}: {e}", exc_info=True)
        await message.reply_text(f"There was an issue with the AI model while processing your CV: {e}. Please try again later.")
        return ConversationHandler.END # End conversation on LLM error for now
    except ConfigError as e: # Catch if ensure_llm_client_configured fails
        logger.critical(f"Configuration error during CV handling: {e}", exc_info=True)
        await message.reply_text("A critical configuration error occurred. The bot admin has been notified. Please try again later.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Unexpected error handling CV for user {user.id}, file {file_name}: {e}", exc_info=True)
        await message.reply_text("An unexpected error occurred while processing your CV. Please try again.")
        return ASK_CV


async def handle_question_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles user's answer to a question and asks the next one."""
    user = update.message.from_user
    answer = update.message.text

    current_index = context.user_data.get('current_question_index', 0)
    questions = context.user_data.get('questions', [])

    if not questions or current_index >= len(questions):
        await update.message.reply_text("Hmm, something went wrong with the questions. Let's restart the CV process.")
        logger.warning(f"User {user.id} in handle_question_answer but no questions/index out of bounds.")
        # Potentially clear user_data related to questions
        return ASK_CV # Or ConversationHandler.END and ask to /start again

    # Store the answer
    # For simplicity, using the question itself as a key, or a generic "answer_X"
    question_answered = questions[current_index]
    context.user_data['answers'][f"answer_to_{current_index+1}_{question_answered[:20]}"] = answer
    logger.info(f"User {user.id} answered Q{current_index+1} ('{question_answered[:30]}...') with: '{answer[:50]}...'")

    current_index += 1
    context.user_data['current_question_index'] = current_index

    if current_index < len(questions):
        await update.message.reply_text(questions[current_index])
        return ASK_QUESTIONS
    else:
        await update.message.reply_text("Thanks! That's all the questions I have for now.")
        # All questions answered, process them
        user_preferences = context.user_data.get('answers', {})
        cv_analysis_data = context.user_data.get('cv_analysis', {})

        # Simulate storing combined data
        # In a real app, this would go to job_manager and then to data_storage
        # combined_data = {"cv_analysis": cv_analysis_data, "preferences_via_questions": user_preferences}
        # store_user_preferences(user.id, combined_data) # Placeholder
        logger.info(f"All questions answered by user {user.id}. Preferences collected: {user_preferences}")

        # For now, just confirm and end
        await update.message.reply_text(
            "I have your preferences. I'll start looking for suitable jobs soon! "
            "(Job searching functionality is under development)."
        )
        # Clean up user_data for this conversation if desired
        # for key in ['questions', 'answers', 'current_question_index', 'raw_cv_text', 'cv_analysis']:
        #     context.user_data.pop(key, None)
        return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays help information."""
    user = update.message.from_user
    logger.info(f"User {user.id} requested /help.")
    await update.message.reply_text(
        "Here's how to use the AI Job Application Agent:\n"
        "- /start: Begin the process by uploading your CV.\n"
        "- /cancel: Stop the current operation (like CV submission or answering questions).\n"
        "- /help: Show this help message.\n\n"
        "Simply follow the prompts after starting. I'll guide you through!"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation."""
    user = update.message.from_user
    logger.info(f"User {user.id} ({user.username}) cancelled the conversation with /cancel.")
    await update.message.reply_text(
        "Okay, the current operation has been cancelled. "
        "You can start over by sending /start anytime."
    )
    # Clean up user_data for this conversation
    for key in ['questions', 'answers', 'current_question_index', 'raw_cv_text', 'cv_analysis']:
        context.user_data.pop(key, None)
    return ConversationHandler.END

# --- Bot Setup and Control Functions ---
def setup_bot() -> Optional[Application]:
    """
    Builds and configures the Telegram Application instance with handlers.
    Does not start polling.

    Returns:
        Application: The configured PTB Application instance, or None if setup fails.
    """
    logger.info("Setting up Telegram bot application...")
    try:
        bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            logger.critical("TELEGRAM_BOT_TOKEN not found or not set in config.py. Bot cannot be configured.")
            # Raise ConfigError so main.py can catch it if called from there
            # Or handle it here if run_bot is called standalone and exit.
            raise ConfigError("TELEGRAM_BOT_TOKEN is missing or not set in the configuration.")

        application = ApplicationBuilder().token(bot_token).build()

        # Conversation Handler for CV submission and questions
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start_command)],
            states={
                ASK_CV: [MessageHandler(filters.ATTACHMENT | filters.Document.ALL, handle_cv_upload)],
                ASK_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question_answer)],
            },
            fallbacks=[CommandHandler("cancel", cancel_command), CommandHandler("help", help_command)],
        )

        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("help", help_command))

        logger.info("Telegram bot application configured with handlers.")
        return application

    except ConfigError:
        # Re-raise ConfigError to be caught by the caller (e.g., main.py or standalone test)
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred during bot setup: {e}", exc_info=True)
        # Wrap other exceptions in a generic TelegramBotError or re-raise if specific handling is needed
        raise TelegramBotError(f"Bot setup failed due to an unexpected error: {e}") from e

async def start_bot_async(application: Application) -> None:
    """
    Initializes, starts the application, and begins polling.
    Args:
        application (Application): The configured PTB Application instance.
    """
    if not application:
        logger.error("Application object is None, cannot start bot.")
        return

    logger.info("Starting bot polling (asynchronously)...")
    try:
        await application.initialize()
        await application.start()
        # updater.start_polling is a blocking call that runs in its own thread.
        # It's not an awaitable, so we don't await it directly in the typical async/await sense.
        # The Application's start() method typically handles the updater lifecycle.
        # If we need to start polling explicitly on the updater (e.g. for drop_pending_updates):
        if application.updater:
            application.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot updater started polling for new updates.")
        else:
            logger.warning("Application updater not found. Polling might not have started as expected.")

        # Keep this function alive if it's the main task for polling,
        # or ensure main.py keeps the event loop running.
        # For now, assuming polling runs in background threads managed by PTB.
        logger.info("Bot has started and is now polling.")

    except Exception as e:
        logger.critical(f"An error occurred while starting bot polling: {e}", exc_info=True)
        # Potentially try to shut down if partially started
        await shutdown_bot_async(application) # Attempt graceful shutdown
        raise TelegramBotError(f"Failed to start bot polling: {e}") from e


async def shutdown_bot_async(application: Application) -> None:
    """
    Gracefully shuts down the Telegram bot application.
    Args:
        application (Application): The PTB Application instance.
    """
    if not application:
        logger.warning("Application object is None, cannot shutdown.")
        return

    logger.info("Attempting to shut down the Telegram bot...")
    try:
        if application.updater and application.updater.running:
            logger.info("Stopping updater polling...")
            application.updater.stop() # This is synchronous
            logger.info("Updater polling stopped.")

        if application.running: # PTB v20 check
            logger.info("Stopping application...")
            await application.stop()
            logger.info("Application stopped.")

        logger.info("Shutting down application...")
        await application.shutdown()
        logger.info("Telegram bot application shut down successfully.")

    except Exception as e:
        logger.error(f"An error occurred during bot shutdown: {e}", exc_info=True)
        # Even if errors occur, it's usually best to let it try to complete.


# Old run_bot function is removed.

if __name__ == '__main__':
    import logging
    import asyncio

    # Basic logging setup for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    logger.info("Running telegram_bot.py directly for testing (async)...")

    async def main_test():
        application = None # Ensure application is defined for finally block
        try:
            # 1. Configure LLM (needed by handlers)
            logger.info("Configuring LLM client for standalone test...")
            await ensure_llm_client_configured()
            logger.info("LLM client configured.")

            # 2. Setup Bot
            logger.info("Setting up bot for standalone test...")
            application = setup_bot() # This can raise ConfigError

            if application:
                # 3. Start Bot
                logger.info("Starting bot asynchronously for standalone test...")
                await start_bot_async(application)

                logger.info("Bot should be running. Press Ctrl+C to stop.")
                # Keep the test running until interrupted
                while True:
                    await asyncio.sleep(5) # Check for interrupt every 5s
            else:
                logger.error("Failed to setup bot for standalone test. Application is None.")

        except ConfigError as e:
            logger.critical(f"Configuration error in standalone test: {e}. Bot cannot run.")
        except KeyboardInterrupt:
            logger.info("Standalone test interrupted by user (Ctrl+C).")
        except Exception as e:
            logger.error(f"Error in standalone test's main_test function: {e}", exc_info=True)
        finally:
            if application:
                logger.info("Shutting down bot in standalone test...")
                await shutdown_bot_async(application)
            logger.info("Standalone test finished.")

    try:
        asyncio.run(main_test())
    except RuntimeError as e: # Handle cases like trying to run asyncio.run() when a loop is already running
        if "cannot call run when a loop is already running" in str(e):
            logger.warning(f"Asyncio loop already running. This can happen in some environments (e.g. Jupyter). {e}")
        else:
            raise
