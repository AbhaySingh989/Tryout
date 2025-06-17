# AI Job Application Agent

## Overview
This AI Job Application Agent is a Python-based tool designed to assist in the process of finding and applying for jobs. It leverages `Crawl4ai` for web scraping tasks and aims to utilize Large Language Models (LLMs) like Google's GEMINI 1.5 Flash for intelligent data extraction, analysis, and (in the future) interaction. The agent's goal is to streamline parts of the job search workflow, with user interaction primarily handled via a Telegram bot interface.

## Core Modules & Responsibilities (Simplified)

*   **`cv_parser`**: Extracts information from CVs.
*   **`llm_interface`**: Handles interactions with LLMs (e.g., Gemini) for tasks like analysis and content generation.
*   **`telegram_bot`**: Manages the Telegram bot interface for user interaction.
*   **`web_scraper`**: Responsible for scraping job postings using `Crawl4ai`.
*   **`job_manager`**: Manages job application data and lifecycle.
*   **`data_storage`**: Handles storage of user profiles and job data (initially JSON).
*   **`error_handler`**: Centralized error logging and management.
*   **`config`**: Manages configuration like API keys.
*   **`main`**: Entry point of the application.
*   **`utils`**: Utility functions.

## Current Capabilities / Features

*   **Job Scraping (Static Site):** Scrapes job postings from a static test site (`https://realpython.github.io/fake-jobs/`) using `Crawl4ai` to extract job details.
*   **LinkedIn Job Search:** Searches for jobs on LinkedIn using `Crawl4ai` based on keywords and location. This relies on CSS selectors for publicly available data and is subject to changes in LinkedIn's website structure.
*   **Conceptual Job Application (`apply_for_job_on_site`):** This function outlines the conceptual steps for automating job applications. However, it is currently a **placeholder** and **not functional** for submitting actual applications. This is due to the significant complexities of web form interaction, CAPTCHA handling, and the current unknown interaction capabilities of `Crawl4ai`.
*   **CV Parsing:** Extracts text from PDF and DOCX CVs.
*   **LLM Interaction (Gemini):** Can analyze CV text and generate questions for user clarification via the `llm_interface`.
*   **Telegram Bot Interface:** Allows users to submit CVs, answer questions, and initiate job searches.

## Technologies Used (Key Libraries)

*   **Web Scraping & Interaction:**
    *   `Crawl4ai`: Primary library for web scraping and crawling.
    *   `requests` (Potentially used by Crawl4ai or for direct simple calls)
    *   `BeautifulSoup4` (Potentially used by Crawl4ai or for direct simple parsing)
*   **LLM Interaction:**
    *   `google-generativeai` (for Gemini 1.5 Flash API)
*   **Telegram Bot:**
    *   `python-telegram-bot`
*   **CV Parsing:**
    *   `pypdf2`
    *   `python-docx`
*   **General:**
    *   Python 3.8+
    *   `logging`

## High-Level Operational Flow

1.  **Initiation & CV Submission (Telegram):** User uploads CV via Telegram.
2.  **CV Parsing & Analysis (`cv_parser`, `llm_interface`):** CV content is extracted and analyzed by Gemini to identify skills and generate clarifying questions.
3.  **User Input (`telegram_bot`):** User answers questions to define job preferences.
4.  **Job Search (`web_scraper` with `Crawl4ai`):** Agent searches sites like the fake jobs portal and LinkedIn based on user profile.
5.  **Presenting Jobs (`telegram_bot`):** User is informed about found jobs.
6.  **(Conceptual) Application Automation (`web_scraper`):** The `apply_for_job_on_site` function outlines how this might work but is **not currently implemented** for actual submissions.
7.  **Status Updates & Error Handling:** User is kept informed via Telegram.

## How to Setup Agent (Windows - Beginner Friendly)

### Prerequisites
*   Windows 10 or 11.
*   A Telegram account.
*   A Google account (for Gemini API access via Google AI Studio).
*   A text editor (like VS Code, Notepad++, or Sublime Text).

### 1. Install Python
*   Go to [https://www.python.org/downloads/](https://www.python.org/downloads/).
*   Download Python (e.g., Python 3.9+).
*   Run installer, **check "Add Python to PATH"**.
*   Verify: Open Command Prompt, type `python --version` and `pip --version`.

### 2. Install Git
*   Go to [https://git-scm.com/downloads](https://git-scm.com/downloads).
*   Download and install Git for Windows.
*   Verify: Open Command Prompt, type `git --version`.

### 3. Clone the Repository
*   Open Command Prompt.
*   Navigate to your desired directory (e.g., `cd C:\Users\YourUser\Documents`).
*   Clone: `git clone <repository_url>` (Replace `<repository_url>` with the project's actual URL).
*   Navigate into the project: `cd job-application-agent`

### 4. Set Up a Virtual Environment
*   Create: `python -m venv venv`
*   Activate: `venv\Scripts\activate`
*   `(venv)` should appear in your prompt.

### 5. Install Dependencies
*   With `venv` active: `pip install -r requirements.txt`
    *   This installs `Crawl4ai` and all other necessary libraries.

### 6. Obtain API Keys and Tokens
*   **Gemini API Key:**
    *   Go to Google AI Studio: [https://aistudio.google.com/](https://aistudio.google.com/)
    *   Sign in, create a new API key. Copy it.
*   **Telegram Bot Token:**
    *   In Telegram, search for "BotFather".
    *   Type `/newbot`, follow instructions. Copy the token.

### 7. Configure the Agent
*   Locate `job_application_agent/config.py`. If it doesn't exist, you might need to create it from a template or copy `config.py.example` to `config.py`.
*   Open `job_application_agent/config.py` and fill in your keys:
    ```python
    # job_application_agent/config.py
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    LOG_FILE_PATH = "job_application_agent/logs/app.log"
    LOG_LEVEL = "INFO"
    DATA_STORAGE_PATH = "job_application_agent/data/"
    # SELENIUM_WEBDRIVER_PATH is no longer actively used by the core agent logic relying on Crawl4ai.
    # Crawl4ai manages its own browser interactions.
    SELENIUM_WEBDRIVER_PATH = ""
    POLITE_REQUEST_DELAY_SECONDS = 2
    ```
*   Replace placeholders with your actual keys.
*   **Do not commit `config.py` with your actual keys to public version control.**

### 8. Running the Agent
*   Ensure virtual environment is active.
*   Navigate to the project directory.
*   Run: `python main.py`
*   Interact with your bot on Telegram.

### 9. Troubleshooting Common Issues
*   **`ModuleNotFoundError`:** Ensure `venv` is active and `pip install -r requirements.txt` was successful.
*   **API Key Errors:** Double-check keys in `config.py`.
*   **`Crawl4ai` issues:** Check `Crawl4ai`'s documentation if specific crawling errors occur. It might require certain system dependencies for browser automation if not using a cloud mode.
*   **Telegram Bot Not Responding:** Verify token and internet connection. Check console logs.

## Addressing Tool Limitations (Focus on `Crawl4ai`)

*   **Rate Limiting (Web Scraping):**
    *   **Mitigation:** Use polite delays (see `POLITE_REQUEST_DELAY_SECONDS` in `config.py`). `Crawl4ai` might have its own mechanisms; refer to its documentation.
*   **CAPTCHAs (Web Scraping & Interaction):**
    *   **Issue:** A major hurdle for automation.
    *   **Mitigation:** `Crawl4ai`'s ability to handle these is unknown. The agent currently does **not** implement CAPTCHA solving. Automated application submission will likely fail if CAPTCHAs are encountered.
*   **Website Structure Changes:**
    *   **Issue:** CSS selectors for LinkedIn (and other sites) can break.
    *   **Mitigation:** Selectors might need manual updates. Future LLM-based extraction via `Crawl4ai` could offer more resilience.
*   **LLM API Usage Limits (Gemini):**
    *   **Mitigation:** Be mindful of free tier limits. Design efficient prompts.
*   **Dynamic Content & JavaScript-Heavy Websites:**
    *   **Mitigation:** `Crawl4ai` is designed to handle JavaScript-heavy sites, which is a key reason for its adoption over simpler libraries for complex targets like LinkedIn.

## Future Development

*   **Explore `Crawl4ai` Advanced Features:** Investigate and leverage `Crawl4ai`'s potential for more robust and intelligent data extraction, possibly using its LLM-integration capabilities (e.g., with a model like GEMINI 1.5 Flash) to move beyond CSS selectors for sites like LinkedIn.
*   **Web Interaction for Applications:** If `Crawl4ai` provides reliable and controllable web interaction features (form filling, button clicks), revisit the `apply_for_job_on_site` function for a more functional implementation, while carefully considering ethical implications and robustness.
*   **Enhanced Error Handling & Recovery:** Improve how the agent handles scraping errors or unexpected website changes.
*   **Broader Platform Support:** Extend scraping capabilities to other job platforms.
*   **Database Integration:** Transition from JSON to SQLite or another database for more robust data management.
