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

# --- Main Bot Function ---
def run_bot():
    """Runs the Telegram bot."""
    logger.info("Attempting to run the Telegram bot...")
    try:
        bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            logger.critical("TELEGRAM_BOT_TOKEN not found or not set in config.py. Bot cannot start.")
            raise ConfigError("TELEGRAM_BOT_TOKEN is missing or not set in the configuration.")

        # It's good practice to call LLM client config once at startup
        # However, ensure_llm_client_configured() is async, so it can't be directly called here (sync context)
        # This means it will be called on first use in an async handler.
        # Alternatively, run_bot could be made async and use asyncio.run()

        application = ApplicationBuilder().token(bot_token).build()

        # Conversation Handler for CV submission and questions
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start_command)],
            states={
                ASK_CV: [MessageHandler(filters.ATTACHMENT | filters.Document.ALL, handle_cv_upload)],
                ASK_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question_answer)],
                # No explicit HANDLE_ANSWERS state if processing happens directly after last question.
            },
            fallbacks=[CommandHandler("cancel", cancel_command), CommandHandler("help", help_command)],
            # per_user=True, per_chat=True # Default, good for user-specific data
        )

        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("help", help_command)) # Also make help available outside conversation

        logger.info("Telegram bot handlers configured. Starting polling...")
        application.run_polling()
        logger.info("Telegram bot has stopped polling.")

    except ConfigError as e:
        logger.critical(f"Bot startup failed due to configuration error: {e}")
        # No way to inform user via bot if token is missing, so just log.
    except Exception as e:
        logger.critical(f"An unexpected error occurred while trying to run the bot: {e}", exc_info=True)

if __name__ == '__main__':
    # This is for direct execution of telegram_bot.py, useful for development/testing the bot.
    # Ensure your config.py is correctly set up with API keys.

    # Basic logging setup if running standalone (error_handler.setup_logging would be better)
    # but error_handler's setup_logging needs config values itself.
    # For simplicity here, just basic Python logging.
    # In a real run, main.py would call error_handler.setup_logging() first.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    logger.info("Running telegram_bot.py directly for testing...")
    # Attempt to configure LLM client here for testing if running standalone
    # This needs an event loop to run configure_llm_client which is async
    import asyncio
    try:
        asyncio.run(ensure_llm_client_configured())
        logger.info("LLM client configured for standalone test run.")
    except Exception as e:
        logger.error(f"Failed to configure LLM client for standalone test: {e}")
        logger.warning("LLM features might not work if client isn't configured.")

    run_bot()
