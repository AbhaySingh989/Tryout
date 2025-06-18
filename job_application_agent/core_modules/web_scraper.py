import time
import urllib.parse # Added for URL encoding
from typing import List, Dict, Optional, Any

from crawl4ai import Crawl4ai # Added crawl4ai import

# Commented out Selenium imports
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.firefox.service import Service as FirefoxService
# # from selenium.webdriver.edge.service import Service as EdgeService # Example for Edge
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from job_application_agent import config
from job_application_agent.core_modules.error_handler import WebScraperError, ConfigError, get_logger

logger = get_logger(__name__)

# _driver_instance: Optional[webdriver.Remote] = None # Commented out Selenium global driver instance

# Commented out Selenium get_webdriver function
# def get_webdriver(browser: str = "chrome", headless: bool = True) -> webdriver.Remote:
#     """
#     Initializes and returns a Selenium WebDriver instance.
#
#     Args:
#         browser (str): The browser to use ('chrome', 'firefox'). Default is 'chrome'.
#         headless (bool): Whether to run the browser in headless mode. Default is True.
#
#     Returns:
#         webdriver.Remote: The initialized Selenium WebDriver instance.
#
#     Raises:
#         ConfigError: If SELENIUM_WEBDRIVER_PATH is specified but invalid.
#         WebScraperError: If WebDriver fails to initialize for other reasons.
#     """
#     global _driver_instance
#     # For simplicity in this phase, we are not reusing _driver_instance globally.
#     # Each call to get_webdriver() will create a new instance.
#     # Proper driver lifecycle management (e.g. a singleton or context manager)
#     # would be needed for more advanced scenarios.
#
#     driver_path = getattr(config, 'SELENIUM_WEBDRIVER_PATH', "")
#     service_instance = None
#
#     options: Optional[webdriver.ChromeOptions | webdriver.FirefoxOptions] = None
#
#     logger.info(f"Attempting to initialize {browser} WebDriver. Headless: {headless}")
#     logger.debug(f"Configured WebDriver path: '{driver_path if driver_path else 'Not set, using PATH'}'")
#
#     try:
#         if browser.lower() == "chrome":
#             options = webdriver.ChromeOptions()
#             if headless:
#                 options.add_argument("--headless")
#             options.add_argument("--disable-gpu") # Recommended for headless
#             options.add_argument("--window-size=1920,1080") # Specify window size
#             options.add_argument("--no-sandbox") #Bypass OS security model, V.IMP
#             options.add_argument("--disable-dev-shm-usage") #overcome limited resource problems
#
#             if driver_path:
#                 service_instance = ChromeService(executable_path=driver_path)
#                 driver = webdriver.Chrome(service=service_instance, options=options)
#             else: # Assumes chromedriver is in PATH
#                 driver = webdriver.Chrome(options=options)
#
#         elif browser.lower() == "firefox":
#             options = webdriver.FirefoxOptions()
#             if headless:
#                 options.add_argument("--headless")
#             options.add_argument("--disable-gpu")
#             options.add_argument("--window-size=1920,1080")
#
#             if driver_path:
#                 service_instance = FirefoxService(executable_path=driver_path)
#                 driver = webdriver.Firefox(service=service_instance, options=options)
#             else: # Assumes geckodriver is in PATH
#                 driver = webdriver.Firefox(options=options)
#         else:
#             raise WebScraperError(f"Unsupported browser: {browser}. Supported browsers are 'chrome', 'firefox'.")
#
#         logger.info(f"{browser.capitalize()} WebDriver initialized successfully.")
#         return driver
#
#     except WebDriverException as e:
#         logger.error(f"Failed to initialize Selenium WebDriver for {browser}: {e}", exc_info=True)
#         if "executable needs to be in PATH" in str(e) or "Service " in str(e) and "not found" in str(e):
#             raise ConfigError(
#                 f"WebDriver executable for {browser} not found. "
#                 f"Ensure it's in your system PATH or SELENIUM_WEBDRIVER_PATH ('{driver_path}') in config.py is correct."
#             ) from e
#         raise WebScraperError(f"Failed to initialize Selenium WebDriver for {browser}: {e}")
#     except Exception as e: # Catch any other unexpected error during setup
#         logger.error(f"An unexpected error occurred during WebDriver setup for {browser}: {e}", exc_info=True)
#         raise WebScraperError(f"Unexpected error setting up WebDriver for {browser}: {e}")

def init_crawl4ai_crawler() -> Crawl4ai:
    """
    Initializes and returns a Crawl4ai crawler instance.
    Currently, this uses default initialization for Crawl4ai.
    Future enhancements could include configuration options.
    """
    logger.info("Initializing Crawl4ai crawler...")
    try:
        crawler = Crawl4ai()
        logger.info("Crawl4ai crawler initialized successfully.")
        return crawler
    except Exception as e:
        logger.error(f"Failed to initialize Crawl4ai crawler: {e}", exc_info=True)
        raise WebScraperError(f"Could not initialize Crawl4ai crawler: {e}")


# Commented out Selenium _click_element_when_ready function
# def _click_element_when_ready(driver: webdriver.Remote, by: By, value: str, timeout: int = 10):
#     """Waits for an element to be clickable and then clicks it."""
#     try:
#         element = WebDriverWait(driver, timeout).until(
#             EC.element_to_be_clickable((by, value))
#         )
#         element.click()
#         logger.debug(f"Clicked element located by {by}='{value}'")
#     except TimeoutException:
#         logger.error(f"Timeout waiting for element to be clickable: {by}='{value}'")
#         raise WebScraperError(f"Element not clickable after {timeout}s: {by}='{value}'")
#     except Exception as e:
#         logger.error(f"Error clicking element {by}='{value}': {e}", exc_info=True)
#         raise WebScraperError(f"Could not click element {by}='{value}': {e}")

def search_jobs_fake_python_static_site(job_title_keywords: Optional[List[str]] = None, location_keywords: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Searches for jobs on the 'https://realpython.github.io/fake-jobs/' static site using Crawl4ai.

    Args:
        browser (str): The browser to use ('chrome', 'firefox'). Default is 'chrome'.
        headless (bool): Whether to run the browser in headless mode. Default is True.

    Returns:
        webdriver.Remote: The initialized Selenium WebDriver instance.

    Raises:
        ConfigError: If SELENIUM_WEBDRIVER_PATH is specified but invalid.
        WebScraperError: If WebDriver fails to initialize for other reasons.
    """
    global _driver_instance
    # For simplicity in this phase, we are not reusing _driver_instance globally.
    # Each call to get_webdriver() will create a new instance.
    # Proper driver lifecycle management (e.g. a singleton or context manager)
    # would be needed for more advanced scenarios.

    driver_path = getattr(config, 'SELENIUM_WEBDRIVER_PATH', "")
    service_instance = None

    options: Optional[webdriver.ChromeOptions | webdriver.FirefoxOptions] = None

    logger.info(f"Attempting to initialize {browser} WebDriver. Headless: {headless}")
    logger.debug(f"Configured WebDriver path: '{driver_path if driver_path else 'Not set, using PATH'}'")

    try:
        if browser.lower() == "chrome":
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu") # Recommended for headless
            options.add_argument("--window-size=1920,1080") # Specify window size
            options.add_argument("--no-sandbox") #Bypass OS security model, V.IMP
            options.add_argument("--disable-dev-shm-usage") #overcome limited resource problems

            if driver_path:
                service_instance = ChromeService(executable_path=driver_path)
                driver = webdriver.Chrome(service=service_instance, options=options)
            else: # Assumes chromedriver is in PATH
                driver = webdriver.Chrome(options=options)

        elif browser.lower() == "firefox":
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            if driver_path:
                service_instance = FirefoxService(executable_path=driver_path)
                driver = webdriver.Firefox(service=service_instance, options=options)
            else: # Assumes geckodriver is in PATH
                driver = webdriver.Firefox(options=options)
        else:
            raise WebScraperError(f"Unsupported browser: {browser}. Supported browsers are 'chrome', 'firefox'.")

        logger.info(f"{browser.capitalize()} WebDriver initialized successfully.")
        return driver

    except WebDriverException as e:
        logger.error(f"Failed to initialize Selenium WebDriver for {browser}: {e}", exc_info=True)
        if "executable needs to be in PATH" in str(e) or "Service " in str(e) and "not found" in str(e):
            raise ConfigError(
                f"WebDriver executable for {browser} not found. "
                f"Ensure it's in your system PATH or SELENIUM_WEBDRIVER_PATH ('{driver_path}') in config.py is correct."
            ) from e
        raise WebScraperError(f"Failed to initialize Selenium WebDriver for {browser}: {e}")
    except Exception as e: # Catch any other unexpected error during setup
        logger.error(f"An unexpected error occurred during WebDriver setup for {browser}: {e}", exc_info=True)
        raise WebScraperError(f"Unexpected error setting up WebDriver for {browser}: {e}")


def _click_element_when_ready(driver: webdriver.Remote, by: By, value: str, timeout: int = 10):
    """Waits for an element to be clickable and then clicks it."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        logger.debug(f"Clicked element located by {by}='{value}'")
    except TimeoutException:
        logger.error(f"Timeout waiting for element to be clickable: {by}='{value}'")
        raise WebScraperError(f"Element not clickable after {timeout}s: {by}='{value}'")
    except Exception as e:
        logger.error(f"Error clicking element {by}='{value}': {e}", exc_info=True)
        raise WebScraperError(f"Could not click element {by}='{value}': {e}")

def search_jobs_fake_python_static_site(job_title_keywords: Optional[List[str]] = None, location_keywords: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Searches for jobs on the 'https://realpython.github.io/fake-jobs/' static site.

    Args:
        job_title_keywords (Optional[List[str]]): Keywords to filter job titles by (case-insensitive).
        location_keywords (Optional[List[str]]): Keywords to filter locations by (case-insensitive).

    Returns:
        List[Dict[str, str]]: A list of job dictionaries, each containing
        'title', 'company', 'location', 'description_snippet', and 'url' (which will be the main site URL for all jobs on this fake site).
    """
    target_url = "https://realpython.github.io/fake-jobs/"
    logger.info(f"Starting job search on Fake Python Jobs site using Crawl4ai: {target_url}")

    jobs_found: List[Dict[str, str]] = []
    crawler = init_crawl4ai_crawler()

    # Define the structure for Crawl4ai to extract data
    # Based on the previous Selenium selectors:
    # - Job cards: `div.card-content`
    # - Title: `h2.title.is-5`
    # - Company: `h3.subtitle.is-6.company`
    # - Location: `p.location`
    # - Description: `div.content > p` (first p)
    extraction_schema = {
        "jobs": {
            "selector": "div.card-content",
            "type": "list",
            "schema": {
                "title": {"selector": "h2.title.is-5", "type": "text"},
                "company": {"selector": "h3.subtitle.is-6.company", "type": "text"},
                "location": {"selector": "p.location", "type": "text"},
                # For description, Crawl4ai might need a more specific selector or post-processing
                # if it grabs all <p> tags within div.content.
                # Let's assume it gets the first one or we can process it.
                "description_raw": {"selector": "div.content p", "type": "text"},
            }
        }
    }

    try:
        logger.debug(f"Running Crawl4ai on {target_url} with schema.")
        # output = crawler.run(url=target_url, parser_config={"schema": extraction_schema}) # Older API
        # Assuming the new API is crawler.crawl(url=target_url, output_format="json", extraction_schema=extraction_schema)
        # Or crawler.run(url=target_url, extraction_schema=extraction_schema)
        # For now, let's assume crawler.run() is the method and it returns a dictionary
        # with a 'data' key containing the extracted information.
        # The exact API usage might need to be verified from crawl4ai documentation.
        # For the purpose of this example, let's simulate a successful run
        # result = crawler.run(url=target_url, extraction_schema=extraction_schema) # Placeholder for actual crawl4ai call

        # Let's try to use the direct crawl method if available and parse its output
        # This is a guess based on common patterns, actual API might differ.
        crawler_output = crawler.crawl(url=target_url, extraction_schema=extraction_schema)

        # Check if crawler_output has the expected structure
        if not crawler_output or 'extracted_data' not in crawler_output or 'jobs' not in crawler_output['extracted_data']:
            logger.warning(f"Crawl4ai did not return the expected data structure for {target_url}. Output: {crawler_output}")
            return []

        extracted_jobs = crawler_output['extracted_data']['jobs']
        logger.info(f"Crawl4ai extracted {len(extracted_jobs)} job items from the page.")

        for job_data in extracted_jobs:
            title = job_data.get("title", "").strip()
            company = job_data.get("company", "").strip()
            location = job_data.get("location", "").strip()
            # Assuming description_raw contains the text from the first <p>
            # If it's a list or combined text, adjustments might be needed.
            description_snippet = job_data.get("description_raw", "").strip()[:200] + "..."

            # Filtering
            title_match = True
            if job_title_keywords:
                title_match = any(keyword.lower() in title.lower() for keyword in job_title_keywords)

            location_match = True
            if location_keywords:
                location_match = any(keyword.lower() in location.lower() for keyword in location_keywords)

            if title_match and location_match:
                jobs_found.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "description_snippet": description_snippet,
                    "url": target_url # This site doesn't have individual job URLs
                })
                logger.debug(f"Matched job: {title} at {company} in {location}")

        logger.info(f"Found {len(jobs_found)} jobs matching criteria on {target_url} using Crawl4ai.")
        return jobs_found

    except Exception as e: # Catch any exception from Crawl4ai or processing
        logger.error(f"An error occurred while scraping {target_url} with Crawl4ai: {e}", exc_info=True)
        # Consider if crawl4ai has specific exceptions to catch
        raise WebScraperError(f"Error scraping {target_url} with Crawl4ai: {e}")
    # No finally block to quit driver as Crawl4ai manages its own resources or doesn't need explicit closing in this context.

# --- LinkedIn Job Search Implementation ---
def search_jobs_linkedin(job_title: str, location: str) -> List[Dict[str, str]]:
    """
    Searches for jobs on LinkedIn using Crawl4ai.

    Args:
        job_title (str): The job title to search for.
        location (str): The location to search for.

    Returns:
        List[Dict[str, str]]: A list of job dictionaries, each containing
        'title', 'company', 'location', and 'url'. Returns an empty list on error or if no jobs found.
    """
    if not job_title:
        logger.warning("LinkedIn search requires a job title.")
        return []

    # Construct search URL
    # Example: https://www.linkedin.com/jobs/search/?keywords=Software%20Engineer&location=Remote
    base_url = "https://www.linkedin.com/jobs/search/"
    params = {}
    params['keywords'] = job_title
    if location: # Location is optional for LinkedIn search, but good to have
        params['location'] = location

    query_string = urllib.parse.urlencode(params)
    target_url = f"{base_url}?{query_string}"

    logger.info(f"Starting LinkedIn job search for '{job_title}' in '{location or 'any location'}' using URL: {target_url}")

    jobs_found: List[Dict[str, str]] = []
    try:
        crawler = init_crawl4ai_crawler()

        # --- Extraction Strategy ---
        # LinkedIn is a dynamic site and often uses complex, changing CSS.
        # Public search results might be limited or require scrolling/interaction for full lists.

        # **Option 1: Conceptual LLM-based Extraction (Illustrative)**
        # This is a conceptual example of how one might instruct Crawl4ai if it has strong LLM capabilities.
        # The actual API for this is unknown for Crawl4ai.
        # llm_prompt = f"""
        # Extract all job postings from the LinkedIn job search results page.
        # For each job, identify and return the following information:
        # - title: The full job title.
        # - company: The name of the company offering the job.
        # - location: The geographical location of the job.
        # - url: The direct permalink URL to the LinkedIn job posting.
        # Ensure the URL is the direct link to the job details page on LinkedIn.
        # Focus on publicly visible job postings on the current page.
        # If a job posting seems to be missing one of these fields, try your best or omit that field for that job.
        # Structure the output as a list of JSON objects, where each object represents a job.
        # Example: [{"title": "Software Engineer", "company": "Tech Corp", "location": "San Francisco, CA", "url": "https://www.linkedin.com/jobs/view/..."}]
        # """
        # Assumptions for LLM-based extraction:
        # 1. Crawl4ai might have a parameter like `llm_extraction_prompt` or `llm_schema`.
        # 2. It might use a pre-configured LLM (e.g., "GEMINI 1.5 Flash" if `Crawl4ai` is from Google)
        #    or require API key setup during `Crawl4ai()` initialization (e.g., `Crawl4ai(llm_api_key="...")`).
        #    If specific model selection is possible, it might be like `Crawl4ai(llm_model="gemini-1.5-flash")`.
        # conceptual_llm_output = crawler.crawl(url=target_url, llm_extraction_prompt=llm_prompt) # This is a hypothetical call

        # **Option 2: CSS Selector-based Extraction (Fallback/Practical Approach)**
        # This is more brittle due to LinkedIn's dynamic nature but is a common fallback.
        # Selectors are best guesses and would need verification and maintenance.
        # It's also possible that LinkedIn serves different HTML structures to different users/bots.
        extraction_schema = {
            "job_postings": {
                "selector": "ul.jobs-search__results-list > li.jobs-search-results__list-item, div.job-search-card", # Common list item selectors
                "type": "list",
                "schema": {
                    "title": {"selector": "h3.base-search-card__title, a.job-card-list__title", "type": "text"},
                    "company": {"selector": "h4.base-search-card__subtitle, a.job-card-container__company-name", "type": "text"},
                    "location": {"selector": "span.job-search-card__location", "type": "text"},
                    # URL is often in an 'a' tag that might also contain the title.
                    # We might need to get the 'href' attribute specifically.
                    # Crawl4ai's 'url' type or 'attribute' extraction would be useful here.
                    # Assuming "type": "link" or similar extracts href from the first 'a' tag.
                    "url": {"selector": "a.base-card__full-link, a.job-card-list__title, a.job-card-container__link", "type": "link"}
                }
            }
        }
        # Note: Crawl4ai might require JavaScript rendering for LinkedIn.
        # If `Crawl4ai()` by default doesn't handle JS-heavy pages well, there might be an option like:
        # `crawler.crawl(url=target_url, extraction_schema=extraction_schema, execute_javascript=True)`
        # For now, we assume default behavior or that Crawl4ai handles it.

        logger.debug(f"Attempting to crawl LinkedIn URL with CSS selectors: {target_url}")
        # Use a user agent to mimic a browser, as LinkedIn is sensitive to bots
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # The actual API for passing headers to crawl4ai.crawl might differ.
        # It could be crawler.crawl(..., headers=headers) or set globally on the crawler instance.
        # For this example, let's assume it's a parameter to crawl() or handled by Crawl4ai internally.
        # This is a placeholder for how headers might be passed if needed.
        # crawler_output = crawler.crawl(url=target_url, extraction_schema=extraction_schema, headers=headers)
        crawler_output = crawler.crawl(url=target_url, extraction_schema=extraction_schema)


        if not crawler_output or 'extracted_data' not in crawler_output or 'job_postings' not in crawler_output['extracted_data']:
            logger.warning(f"Crawl4ai did not return the expected data structure for LinkedIn URL: {target_url}. Output: {crawler_output}")
            if crawler_output and "error" in crawler_output: # Check for explicit error messages
                 logger.error(f"Crawl4ai reported an error: {crawler_output['error']}")
            if crawler_output and "status_code" in crawler_output and crawler_output["status_code"] != 200:
                logger.error(f"LinkedIn request failed with status code: {crawler_output['status_code']}. This might indicate an IP block or CAPTCHA.")
            return []

        extracted_jobs = crawler_output['extracted_data']['job_postings']
        logger.info(f"Crawl4ai extracted {len(extracted_jobs)} potential job items from LinkedIn page: {target_url}")

        for job_data in extracted_jobs:
            title = job_data.get("title", "N/A").strip()
            company = job_data.get("company", "N/A").strip()
            location = job_data.get("location", "N/A").strip()
            job_url = job_data.get("url", "").strip()

            # Basic validation: title and URL are important
            if title == "N/A" or not job_url:
                logger.debug(f"Skipping job item due to missing title or URL: {job_data}")
                continue

            # Ensure the URL is absolute. LinkedIn URLs in search results should be absolute.
            if not job_url.startswith("http"):
                logger.warning(f"Found relative URL '{job_url}' for job '{title}'. Attempting to make absolute, but this is unusual for LinkedIn direct links.")
                # This case should ideally not happen if selectors are correct for direct job links.
                # If they are links to an intermediate page, this would be more complex.
                # For now, we'll assume they should be absolute or skip.
                # job_url = urllib.parse.urljoin(base_url, job_url) # Fallback if needed, but risky
                continue


            jobs_found.append({
                "title": title,
                "company": company,
                "location": location,
                "url": job_url
            })
            logger.debug(f"Successfully processed job: {title} at {company}")

        logger.info(f"Found {len(jobs_found)} jobs matching criteria on LinkedIn for '{job_title}'.")
        return jobs_found

    except WebScraperError as e: # Catch errors from init_crawl4ai_crawler
        logger.error(f"WebScraperError during LinkedIn search: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during LinkedIn job search for '{job_title}': {e}", exc_info=True)
        # This could be due to network issues, changes in LinkedIn's site structure, or Crawl4ai internal errors.
        # If LinkedIn blocks due to bot detection, this might also be caught here.
        return []

# --- Job Application Function (Conceptual) ---
def apply_for_job_on_site(job_url: str, user_profile: Dict[str, Any]) -> bool:
    """
    Attempts to apply for a job on a given site using Crawl4ai.
    This is a conceptual outline and currently a placeholder.

    Args:
        job_url (str): The direct URL to the job application page.
        user_profile (Dict[str, Any]): A dictionary containing user information
                                       (e.g., name, email, resume_path).

    Returns:
        bool: True if the application was (conceptually) submitted successfully, False otherwise.
    """
    logger.info(f"Attempting to apply for job at URL: {job_url} with profile: {user_profile.get('name', 'N/A')}")

    try:
        # crawler = init_crawl4ai_crawler() # Initialize crawler if actual interaction were to occur
        logger.info("Crawl4ai initialized (conceptually) for job application.")

        # --- Conceptual Outline for Form Interaction using Crawl4ai ---
        # The following steps are hypothetical and depend on Crawl4ai's capabilities for web interaction,
        # which are not fully known at this time.

        # 1. Navigate to the job application page:
        # logger.debug(f"Navigating to {job_url}...")
        # page_content = crawler.crawl(url=job_url, render_javascript=True) # Assuming JS rendering is often needed
        # if not page_content or "html_content" not in page_content:
        #     logger.error(f"Failed to load page content from {job_url}")
        #     return False

        # 2. Identify form fields:
        # This is the most complex step. Options include:
        #    a. Pre-defined selectors (brittle, site-specific).
        #    b. Heuristic-based identification (e.g., looking for input fields with labels like "Name", "Email").
        #    c. LLM-assisted identification (conceptual):
        #       - If Crawl4ai supports it, an LLM (e.g., GEMINI 1.5 Flash, if configurable) could be prompted.
        #       - Example prompt to Crawl4ai (hypothetical):
        #         llm_form_analysis_prompt = f"""
        #         Analyze the HTML content of the page at {job_url}.
        #         Identify all input fields relevant for a job application.
        #         For each field, provide:
        #         - A robust CSS selector.
        #         - The type of field (e.g., text, email, file, textarea, select).
        #         - The most likely corresponding key from this user profile: {list(user_profile.keys())}.
        #         - The visible label text for the field.
        #         Return this as a JSON list.
        #         Example: [{{ "selector": "#firstName", "type": "text", "profile_key": "full_name", "label": "First Name" }}]
        #         """
        #       - field_map = crawler.analyze_form(url=job_url, prompt=llm_form_analysis_prompt) # Hypothetical function

        # 3. Map user_profile data to fields and fill them:
        #    for field_info in field_map:
        #        profile_key = field_info.get("profile_key")
        #        selector = field_info.get("selector")
        #        field_type = field_info.get("type")
        #        value_to_fill = user_profile.get(profile_key)
        #
        #        if value_to_fill and selector:
        #            logger.debug(f"Attempting to fill field '{selector}' with data from profile key '{profile_key}'")
        #            if field_type == "file" and profile_key == "resume_path":
        #                # crawler.upload_file(selector, value_to_fill) # Hypothetical
        #                logger.info(f"Conceptual: Upload file '{value_to_fill}' to selector '{selector}'")
        #            elif field_type in ["text", "email", "textarea"]: # etc.
        #                # crawler.type_text(selector, value_to_fill) # Hypothetical
        #                logger.info(f"Conceptual: Type text '{value_to_fill}' into selector '{selector}'")
        #            # Add handling for select, radio, checkbox etc.
        #        else:
        #            logger.warning(f"Could not map or find value for field: {field_info.get('label')}")

        # 4. Handle "Cover Letter" either as text input or file upload:
        #    If user_profile['cover_letter_text'] exists, find a textarea for it.
        #    If user_profile['cover_letter_path'] exists, find a file upload for it.

        # 5. Find and click the submit button:
        #    submit_button_selector = "#submit-application, button[type='submit'], [aria-label*='Submit']" # Common patterns
        #    # Or using LLM to find it:
        #    # submit_prompt = "Find the main submit button for this job application form."
        #    # submit_selector = crawler.find_element_interactive(url=job_url, prompt=submit_prompt) # Hypothetical
        #    # crawler.click_element(submit_selector) # Hypothetical
        #    logger.info(f"Conceptual: Click submit button (e.g., '{submit_button_selector}')")

        # 6. Confirmation:
        #    Ideally, check for a success message on the next page.
        #    logger.info("Conceptual: Application submitted. Verifying confirmation...")

        # --- Challenges and Feasibility ---
        logger.warning("Automated job application faces significant challenges:")
        logger.warning("- CAPTCHAs: Most sites use CAPTCHAs to prevent automated submissions.")
        logger.warning("- Dynamic Forms & SPAs: Modern web apps change content without full page reloads, complicating selector stability.")
        logger.warning("- Unique Site Structures: Each job portal has a different layout and form structure, requiring site-specific logic (or a very advanced AI).")
        logger.warning("- Session/Login Management: Many applications are behind login walls, requiring authentication.")
        logger.warning("- Ethical Implications & Risks: Automated applications can be seen as spam, may not be tailored well, and errors could misrepresent the applicant.")
        logger.warning("- Robustness: Ensuring the automation correctly fills all required fields, handles errors, and confirms submission is very difficult.")

        logger.warning(f"apply_for_job_on_site for URL {job_url} is a placeholder and has NOT performed any actual web interaction or application submission.")
        return False # Explicitly return False as this is a placeholder

    except WebScraperError as e: # From init_crawl4ai_crawler
        logger.error(f"WebScraperError in apply_for_job_on_site: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred in apply_for_job_on_site for {job_url}: {e}", exc_info=True)
        return False


# --- Example Usage (for testing) ---
if __name__ == '__main__':
    import logging # Import logging for standalone testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    logger.info("--- Web Scraper Standalone Test ---")

    # Test Crawl4ai initialization (replaces WebDriver test for this part)
    try:
        logger.info("Attempting to initialize Crawl4ai for test...")
        init_crawl4ai_crawler() # Test the initialization
        logger.info("Crawl4ai initialized successfully for test.")
        can_test_crawl4ai = True
    except (WebScraperError, Exception) as e: # Catch WebScraperError or any other init error
        logger.error(f"Failed to initialize Crawl4ai for testing: {e}")
        logger.warning("Skipping live scraping tests with Crawl4ai as setup failed.")
        can_test_crawl4ai = False


    # Test scraping the fake jobs site using Crawl4ai
    if can_test_crawl4ai:
        logger.info("\n--- Testing search_jobs_fake_python_static_site with Crawl4ai ---")
        try:
            # Example 1: No keywords (get all jobs)
            all_jobs = search_jobs_fake_python_static_site()
            logger.info(f"Found {len(all_jobs)} total jobs on fake site with Crawl4ai.")
            if all_jobs:
                logger.info(f"First few jobs (no filter):")
                for i, job in enumerate(all_jobs[:3]):
                    logger.info(f"  {i+1}. {job['title']} at {job['company']} in {job['location']}")
            else:
                logger.info("No jobs found on fake site with Crawl4ai (no filter). This might indicate an issue if jobs are expected.")


            # Example 2: With keywords
            logger.info("\nSearching for 'Python Developer' jobs in 'Remote' locations (expecting few/none on this fake site)...")
            filtered_jobs = search_jobs_fake_python_static_site(
                job_title_keywords=["Python Developer", "Engineer"],
                location_keywords=["Remote", "New York"] # This site has "Remote"
            )
            logger.info(f"Found {len(filtered_jobs)} jobs matching title/location keywords with Crawl4ai.")
            if filtered_jobs:
                logger.info("Filtered jobs found:")
                for job in filtered_jobs:
                    logger.info(f"  - {job['title']} at {job['company']} in {job['location']}")
            else:
                logger.info("No jobs found matching the specific title/location keywords on the fake site with Crawl4ai.")

        except WebScraperError as e:
            logger.error(f"WebScraperError during fake site test with Crawl4ai: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during fake site test with Crawl4ai: {e}", exc_info=True)
    else:
        logger.warning("Crawl4ai was not successfully initialized, so live scraping tests were skipped.")


    logger.info("\n--- Testing placeholder functions ---")
    # Test LinkedIn search - this is a live web call
    logger.info("\n--- Testing search_jobs_linkedin (live) ---")
    # Keep this test minimal to avoid excessive requests during development/testing.
    if can_test_crawl4ai: # Only if Crawl4ai initialized successfully
        linkedin_jobs = search_jobs_linkedin("Software Engineer", "Remote") # Using a common but not overly broad term.
        if linkedin_jobs:
            logger.info(f"Found {len(linkedin_jobs)} jobs on LinkedIn for 'Software Engineer' in 'Remote'. First one: {linkedin_jobs[0]['title']} - {linkedin_jobs[0]['url']}")
        else:
            logger.warning("No jobs found on LinkedIn for 'Software Engineer' in 'Remote', or an error occurred. Check logs for details.")
    else:
        logger.warning("Skipping LinkedIn search test as Crawl4ai initialization failed.")

    # Test conceptual apply_for_job_on_site
    logger.info("\n--- Testing apply_for_job_on_site (conceptual) ---")
    dummy_profile = {
        "name": "Test User",
        "email": "test@example.com",
        "resume_path": "/path/to/resume.pdf",
        "cover_letter_text": "I am very interested in this position."
    }
    application_result = apply_for_job_on_site("https://example.com/job/apply/123", dummy_profile)
    logger.info(f"Conceptual job application result: {application_result} (expected False)")
    assert not application_result # Ensure it returns False

    logger.info("\n--- Web Scraper Standalone Test Complete ---")
