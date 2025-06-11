# AI Job Application Agent

## Overview
This AI Job Application Agent is a Python-based tool designed to automate the process of finding and applying for jobs on platforms like LinkedIn and Naukri.com. It leverages the Gemini 1.5 Flash language model for intelligent CV analysis, decision-making, and generating tailored responses. User interaction, including CV submission and answering clarifying questions, is handled through a Telegram bot interface. The agent aims to be modular, readable, and robust, utilizing only free and open-source tools.

## Core Modules & Responsibilities

*   **`cv_parser`**: Parses CVs (in formats like PDF, DOCX) to extract key information such as skills, experience, education, and contact details. This information will be used to tailor applications and match against job requirements.
*   **`llm_interface`**: Handles all interactions with the chosen Large Language Model (e.g., Gemini). This includes sending prompts for tasks like generating cover letters, summarizing job descriptions, and tailoring CVs. It will also manage API calls and responses.
*   **`telegram_bot`**: Implements the Telegram bot interface. It will handle user commands, send notifications (e.g., new job matches, application status updates), and allow users to interact with the agent (e.g., initiate job searches, update profile).
*   **`web_scraper`**: Responsible for scraping job postings from specified websites (e.g., LinkedIn, Indeed, company career pages). It will extract details like job title, description, company, location, and application link.
*   **`job_manager`**: Manages the lifecycle of job applications. This includes tracking applied jobs, stages of application (e.g., applied, interviewing, rejected), and storing relevant metadata for each job.
*   **`data_storage`**: Initially, this will use simple JSON files for storing data like user profiles, job application history, and configurations. It can be extended to use a lightweight database like SQLite if needed.
*   **`error_handler`**: Provides a centralized way to handle errors and exceptions that may occur in different parts of the application. This includes logging errors and potentially sending notifications for critical issues.
*   **`config`**: Manages sensitive information like API keys (Gemini, Telegram), email credentials (if used for notifications or applications), and other configurable parameters. This file should NOT be committed to version control.
*   **`main`**: The main entry point of the application. It will initialize and coordinate the different modules to run the agent.
*   **`utils`**: Contains helper functions and utility classes that are used across different modules. This helps in keeping the codebase DRY (Don't Repeat Yourself).

## Tools and Libraries Used

*   **CV Parsing (`cv_parser`):**
    *   `pypdf2` (for PDF files)
    *   `python-docx` (for DOCX files)
    *   *(Optional, for more advanced text processing)* `spaCy` or `NLTK`
*   **LLM Interaction (`llm_interface`):**
    *   `google-generativeai` (for Gemini 1.5 Flash API)
*   **Telegram Bot (`telegram_bot`):**
    *   `python-telegram-bot`
*   **Web Scraping (`web_scraper`):**
    *   `requests` (for HTTP requests)
    *   `BeautifulSoup4` (for HTML parsing)
    *   `selenium` (for JavaScript-heavy sites and interaction)
*   **Data Handling/Storage (`job_manager`, `data_storage`):**
    *   `json` (built-in Python library for JSON manipulation)
    *   *(Optional, for more complex data)* `pandas`
*   **Error Handling (`error_handler`):**
    *   `logging` (built-in Python library)
*   **General:**
    *   Python 3.8+

## High-Level Operational Flow

The agent operates through a sequence of steps, coordinating various modules to achieve automated job applications:

1.  **Initiation & CV Submission (Telegram):**
    *   The user starts an interaction with the AI agent via the Telegram bot.
    *   The user uploads their CV (e.g., PDF or DOCX format) through the Telegram interface.

2.  **CV Reception & Parsing (`telegram_bot`, `cv_parser`):**
    *   The `telegram_bot` module receives the CV file.
    *   It passes the file to the `cv_parser` module.
    *   `cv_parser` extracts the raw text content from the CV.

3.  **CV Analysis & Skill Extraction (`llm_interface` - Gemini):**
    *   The extracted text is sent to the `llm_interface`.
    *   The `llm_interface` uses the Gemini 1.5 Flash API to analyze the CV, identify key skills, relevant experiences, and educational background.

4.  **Clarification Questions (`llm_interface`, `telegram_bot`):**
    *   Based on the CV analysis and predefined logic, the `llm_interface` (Gemini) generates a set of up to 11 targeted questions. These questions aim to clarify the user's job preferences, desired roles, salary expectations (if comfortable sharing), location preferences, etc.
    *   The `telegram_bot` presents these questions to the user.

5.  **User Input & Preference Storage (`telegram_bot`, `job_manager`, `data_storage`):**
    *   The user provides answers to the questions via Telegram.
    *   The `telegram_bot` collects these answers.
    *   The `job_manager` processes and stores these preferences, along with the extracted CV information, using the `data_storage` module (e.g., in a JSON file).

6.  **Job Search (`web_scraper`):**
    *   The `job_manager` triggers the `web_scraper` module.
    *   The `web_scraper` uses the user's skills (from CV) and preferences (from questions) to search for relevant job postings on configured platforms (LinkedIn, Naukri.com, Workday, etc.).

7.  **Job Filtering & Matching (`job_manager`, `llm_interface`):**
    *   The `web_scraper` returns a list of potential job postings.
    *   The `job_manager` performs initial filtering based on explicit criteria.
    *   For more nuanced matching, relevant job description details can be sent to the `llm_interface` (Gemini) to assess the fit with the user's profile.

8.  **Presenting Jobs to User (`telegram_bot`):**
    *   The `telegram_bot` informs the user about the number of relevant jobs found and can present a summary of these jobs.
    *   (Optional: The agent could ask for user approval before proceeding to apply for specific jobs).

9.  **Application Automation (`web_scraper`, `llm_interface`):**
    *   For approved/selected jobs, the `web_scraper` attempts to automate the application process. This involves:
        *   Navigating to the job application page.
        *   Filling out standard application form fields using the user's stored information.
        *   For custom questions or cover letter requirements, the `llm_interface` (Gemini) can be prompted to help generate appropriate responses or content.

10. **Status Updates & Error Handling (`telegram_bot`, `error_handler`):**
    *   Throughout the entire process, the `telegram_bot` provides real-time status updates to the user (e.g., "Analyzing CV...", "Found X relevant jobs...", "Applying for job Y...", "Application successful/failed for Z").
    *   The `error_handler` module logs any issues encountered (e.g., web scraping errors, API failures, CAPTCHAs).
    *   The `telegram_bot` informs the user of significant errors and, if possible, suggests next steps.

11. **Completion & Reporting:**
    *   The agent reports the final status of all attempted applications to the user via Telegram.
    *   Application history is stored by `data_storage`.

## How to Setup Agent (Windows - Beginner Friendly)

### Prerequisites
*   Windows 10 or 11.
*   A Telegram account.
*   A Google account (for Gemini API access).
*   A web browser (like Chrome or Firefox) for Selenium.
*   A text editor (like VS Code, Notepad++, or Sublime Text) for editing configuration files.

### 1. Install Python
*   Go to the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
*   Download the latest stable Python installer for Windows (e.g., Python 3.9+).
*   Run the installer. **Important:** Check the box that says "Add Python to PATH" during installation.
*   Verify installation: Open Command Prompt (search "cmd") and type `python --version` and `pip --version`. You should see the installed versions.

### 2. Install Git
*   Go to the official Git website: [https://git-scm.com/downloads](https://git-scm.com/downloads)
*   Download and install Git for Windows. You can mostly use the default settings during installation.
*   Verify installation: Open a new Command Prompt and type `git --version`.

### 3. Clone the Repository
*   Open Command Prompt.
*   Navigate to the directory where you want to store the agent (e.g., `cd C:\Users\YourUser\Documents`).
*   Clone the repository: `git clone https://github.com/your-username/job-application-agent.git` (Replace `<repository_url>` with the actual URL once the project is hosted).
### 4. Set Up a Virtual Environment
*   In Command Prompt, navigate into the cloned project directory: `cd job-application-agent`
*   Create a virtual environment: `python -m venv venv`
*   Activate the virtual environment: `venv\Scripts\activate`
*   You should see `(venv)` at the beginning of your command prompt line. This means the virtual environment is active. (To deactivate later, just type `deactivate`).

### 5. Install Dependencies
*   With the virtual environment active, install the required Python libraries:
    `pip install -r requirements.txt`

### 6. Obtain API Keys and Tokens
*   **Gemini API Key:**
    *   Go to Google AI Studio: [https://aistudio.google.com/](https://aistudio.google.com/)
    *   Sign in with your Google account.
    *   Click on "Get API key" and create a new API key.
    *   Copy this key carefully. **Treat it like a password!**
*   **Telegram Bot Token:**
    *   Open Telegram and search for "BotFather".
    *   Start a chat with BotFather by typing `/start`.
    *   Create a new bot by typing `/newbot`.
    *   Follow the instructions to choose a name and username for your bot (the username must end in "bot", e.g., `MyJobAgent_bot`).
    *   BotFather will give you an HTTP API token. Copy this token carefully. **Treat it like a password!**

### 7. Configure the Agent
*   In the project's root directory (`job_application_agent`), you'll find a file named `config.py`.
*   Open `config.py` with your text editor.
*   You will need to add your API keys and other configurations here. The file should have comments guiding you. For example:
    ```python
    # config.py

    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

    # Placeholder for job search preferences - these might be populated by user interaction later
    # or you can set some defaults.
    TARGET_JOB_TITLES = ["Software Engineer", "Python Developer"]
    TARGET_LOCATIONS = ["Remote", "New York"]
    # Add other configurations as needed, e.g., paths for webdrivers if not in PATH

    # Example for Selenium WebDriver (Chrome) - ensure chromedriver.exe is in your PATH
    # or provide the full path to the executable.
    # CHROME_DRIVER_PATH = "C:\path\to\chromedriver.exe" # Uncomment and set if needed
    ```
*   **Important:** Replace `"YOUR_GEMINI_API_KEY_HERE"` and `"YOUR_TELEGRAM_BOT_TOKEN_HERE"` with your actual keys.
*   Save the `config.py` file. **Do not share this file or commit it to version control if it contains your actual keys.** The `.gitignore` file should already be configured to ignore `config.py`.

### 8. (If using Selenium) Setup WebDriver
*   The agent uses Selenium for web scraping dynamic websites. You'll need a WebDriver corresponding to your browser.
*   **For Chrome:**
    *   Check your Chrome browser version (Help -> About Google Chrome).
    *   Download the matching ChromeDriver from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads).
    *   Extract `chromedriver.exe` and place it in a directory that's in your system's PATH (e.g., `C:\Windows\System32` - requires admin, or a custom folder you add to PATH), or place it in the project root, or specify its path in `config.py` (as shown in the example above).
*   **For Firefox:**
    *   Download GeckoDriver from [https://github.com/mozilla/geckodriver/releases](https://github.com/mozilla/geckodriver/releases).
    *   Extract `geckodriver.exe` and place it similarly to ChromeDriver.

### 9. Running the Agent
*   Ensure your virtual environment is active (`venv\Scripts\activate`).
*   Navigate to the project directory in Command Prompt.
*   Run the main script: `python main.py`
*   Open Telegram and find the bot you created. Send it a message (e.g., `/start`) to begin interacting with the agent.

### 10. Troubleshooting Common Issues
*   **`ModuleNotFoundError`:** Make sure your virtual environment is active and you've run `pip install -r requirements.txt`.
*   **API Key Errors:** Double-check that your API keys in `config.py` are correct and do not have extra spaces or characters. Ensure the Gemini API is enabled for your Google Cloud project if that's the source.
*   **WebDriver Errors (Selenium):**
    *   Ensure the WebDriver version matches your browser version.
    *   Make sure the WebDriver executable (`chromedriver.exe` or `geckodriver.exe`) is in your system PATH or its path is correctly specified in `config.py`.
    *   "SessionNotCreatedException": Often a version mismatch or driver not found.
*   **Telegram Bot Not Responding:**
    *   Verify your `TELEGRAM_BOT_TOKEN` is correct.
    *   Check your internet connection.
    *   Look for error messages in the console where `main.py` is running.

## Addressing Free Tool Limitations

*   **Rate Limiting (Web Scraping):**
    *   **Issue:** Job portals and websites often implement rate limiting to prevent abuse, which can block the IP address if too many requests are made in a short period.
    *   **Mitigation:**
        *   The `web_scraper` module will implement polite scraping practices.
        *   Introduce delays (e.g., `time.sleep()`) between requests.
        *   Implement exponential backoff strategies for retrying failed requests due to rate limiting (e.g., wait longer after each subsequent failure).
        *   Vary request headers (e.g., User-Agent) if appropriate and respectful of terms of service.

*   **CAPTCHAs (Web Scraping):**
    *   **Issue:** CAPTCHAs are designed to block automated access and are a significant challenge for web scrapers.
    *   **Mitigation:**
        *   **Primary Strategy:** The agent will attempt to avoid actions that trigger CAPTCHAs by mimicking human-like interaction patterns where possible (e.g., slower actions when using Selenium).
        *   **Detection & Notification:** If a CAPTCHA is detected, the `web_scraper` will log the event. The `telegram_bot` will notify the user that a manual intervention might be required for a specific website or application. The agent might pause operations for that particular site or task.
        *   **Selenium's Role:** For some simpler CAPTCHAs (especially those less reliant on image recognition and more on JavaScript challenges), Selenium itself might bypass them during automated browser interactions. However, this is not guaranteed.
        *   **No Paid Services:** As per constraints, paid CAPTCHA-solving services will *not* be integrated. This means some sites or applications might be impossible to automate fully if CAPTCHAs are consistently encountered and cannot be bypassed by Selenium or human-like interaction emulation.

*   **Website Structure Changes (Web Scraping):**
    *   **Issue:** Websites frequently update their HTML structure. This can break web scrapers that rely on specific CSS selectors or XPath expressions.
    *   **Mitigation:**
        *   **Resilient Selectors:** Aim to use more stable selectors (e.g., those based on IDs or stable attributes rather than highly nested or order-dependent ones).
        *   **Configuration:** Store CSS selectors and XPath expressions in the `config.py` file or a separate configuration file. This allows for easier updates without modifying the core scraper logic.
        *   **Error Reporting:** Implement robust error detection in scrapers. If a scraper fails to find expected elements, it should log the issue clearly (e.g., "Could not find job title element on LinkedIn search page") and notify the user via the `telegram_bot`.
        *   **Regular Maintenance:** Acknowledge that this is an inherent challenge, and the scraping scripts will likely require ongoing maintenance as websites evolve.

*   **LLM API Usage Limits (Gemini 1.5 Flash):**
    *   **Issue:** Free tiers of LLM APIs often have usage limits (e.g., requests per minute, tokens per month).
    *   **Mitigation:**
        *   **Efficient Prompting:** Design prompts to be concise and effective to minimize token usage.
        *   **Caching:** For non-user-specific, repeatable LLM tasks (e.g., generic advice, if any), consider caching results. (Note: Most tasks in this agent are user-specific, so caching might be less applicable here).
        *   **Request Batching/Queuing:** If making many calls, implement a queue and process them respecting API rate limits.
        *   **Error Handling:** Gracefully handle API errors related to rate limits or quotas, potentially retrying with backoff or notifying the user if limits are exhausted.
        *   **Monitor Usage:** Advise the user in the setup guide to be aware of any free tier limits associated with their Gemini API key.

*   **Dynamic Content & JavaScript-Heavy Websites:**
    *   **Issue:** Many modern job portals (like LinkedIn, Workday) rely heavily on JavaScript to load content dynamically. Simple `requests` and `BeautifulSoup` may not be able to access this content.
    *   **Mitigation:**
        *   **Selenium:** The `web_scraper` will use `selenium` to control a web browser programmatically. Selenium can execute JavaScript and interact with dynamic page elements, making it suitable for these sites.
        *   **Targeted Use:** Use Selenium judiciously as it's slower and more resource-intensive than direct HTTP requests. Employ it specifically for pages or parts of pages that require JavaScript rendering.
