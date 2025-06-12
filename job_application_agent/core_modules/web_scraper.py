import time
from typing import List, Dict, Optional, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
# from selenium.webdriver.edge.service import Service as EdgeService # Example for Edge
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from job_application_agent import config
from job_application_agent.core_modules.error_handler import WebScraperError, ConfigError, get_logger

logger = get_logger(__name__)

_driver_instance: Optional[webdriver.Remote] = None # To potentially reuse driver instance if managed globally

def get_webdriver(browser: str = "chrome", headless: bool = True) -> webdriver.Remote:
    """
    Initializes and returns a Selenium WebDriver instance.

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
    logger.info(f"Starting job search on Fake Python Jobs site: {target_url}")

    driver = None # Ensure driver is defined for the finally block
    jobs_found: List[Dict[str, str]] = []

    polite_delay = getattr(config, 'POLITE_REQUEST_DELAY_SECONDS', 2) # Default 2s

    try:
        driver = get_webdriver() # Using default Chrome, headless
        driver.get(target_url)
        time.sleep(polite_delay) # Be polite after page load

        # The jobs are in 'div' elements with class 'card-content'
        # Each job card contains:
        # - h2 class="title is-5" -> Job Title
        # - h3 class="subtitle is-6 company" -> Company
        # - p class="location" -> Location
        # - div class="content" -> p -> Description (first p if multiple)

        # Wait for job cards to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card-content"))
        )

        job_cards = driver.find_elements(By.CLASS_NAME, "card-content")
        logger.info(f"Found {len(job_cards)} job cards on the page.")

        for card in job_cards:
            try:
                title_element = card.find_element(By.CLASS_NAME, "title.is-5")
                company_element = card.find_element(By.CLASS_NAME, "subtitle.is-6.company")
                location_element = card.find_element(By.CLASS_NAME, "location")
                # Description is inside a 'div' with class 'content', then a 'p'
                description_p_element = card.find_element(By.XPATH, ".//div[@class='content']/p") # Relative XPath

                title = title_element.text.strip()
                company = company_element.text.strip()
                location = location_element.text.strip()
                description_snippet = description_p_element.text.strip()[:200] + "..." # First 200 chars

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

            except NoSuchElementException as e:
                logger.warning(f"Could not parse a job card fully, missing element: {e.msg}. Skipping this card.")
            except Exception as e:
                logger.warning(f"Unexpected error parsing a job card: {e}", exc_info=True)

        logger.info(f"Found {len(jobs_found)} jobs matching criteria on {target_url}.")
        return jobs_found

    except TimeoutException as e:
        logger.error(f"Timeout waiting for elements on {target_url}: {e}", exc_info=True)
        raise WebScraperError(f"Timeout accessing {target_url}: {e}")
    except WebDriverException as e: # Catch more general WebDriver errors
        logger.error(f"WebDriver error during scraping {target_url}: {e}", exc_info=True)
        raise WebScraperError(f"WebDriver error scraping {target_url}: {e}")
    except Exception as e: # Catch any other unexpected error
        logger.error(f"An unexpected error occurred while scraping {target_url}: {e}", exc_info=True)
        raise WebScraperError(f"Unexpected error scraping {target_url}: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver quit successfully.")
            except Exception as e:
                logger.error(f"Error quitting WebDriver: {e}", exc_info=True)

# --- Placeholder functions for complex sites ---
def search_jobs_linkedin(job_title: str, location: str) -> List[Dict[str, str]]:
    logger.warning("search_jobs_linkedin is not implemented yet.")
    # Here you would implement LinkedIn specific scraping logic
    # This would involve logging in, handling dynamic content, etc.
    return []

def apply_for_job_on_site(job_url: str, user_profile: Dict[str, Any]) -> bool:
    logger.warning(f"apply_for_job_on_site for URL {job_url} is not implemented yet.")
    # This would involve navigating to the job URL and attempting to fill forms
    # using Selenium, based on user_profile data.
    return False

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    import logging # Import logging for standalone testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    logger.info("--- Web Scraper Standalone Test ---")

    # Test WebDriver initialization
    test_driver = None
    try:
        logger.info("Attempting to initialize WebDriver for test...")
        # You might want to set headless=False here to see the browser window for testing
        test_driver = get_webdriver(headless=True)
        logger.info(f"WebDriver ({test_driver.name}) initialized successfully for test.")
    except (ConfigError, WebScraperError) as e:
        logger.error(f"Failed to initialize WebDriver for testing: {e}")
        logger.warning("Skipping live scraping tests as WebDriver setup failed.")
        # If WebDriver fails, the rest of this test block that needs it won't run.
    finally:
        if test_driver:
            try:
                test_driver.quit()
                logger.info("Test WebDriver quit successfully.")
            except Exception as e:
                logger.error(f"Error quitting test WebDriver: {e}")

    # Test scraping the fake jobs site (only if WebDriver was initialized)
    if test_driver: # This condition won't be met if above failed
        logger.info("\n--- Testing search_jobs_fake_python_static_site ---")
        try:
            # Example 1: No keywords (get all jobs)
            all_jobs = search_jobs_fake_python_static_site()
            logger.info(f"Found {len(all_jobs)} total jobs on fake site.")
            if all_jobs:
                logger.info(f"First few jobs (no filter):")
                for i, job in enumerate(all_jobs[:3]):
                    logger.info(f"  {i+1}. {job['title']} at {job['company']} in {job['location']}")

            # Example 2: With keywords
            logger.info("\nSearching for 'Python Developer' jobs in 'Remote' locations (expecting few/none on this fake site)...")
            filtered_jobs = search_jobs_fake_python_static_site(
                job_title_keywords=["Python Developer", "Engineer"],
                location_keywords=["Remote", "New York"] # This site has "Remote"
            )
            logger.info(f"Found {len(filtered_jobs)} jobs matching title/location keywords.")
            if filtered_jobs:
                logger.info("Filtered jobs found:")
                for job in filtered_jobs:
                    logger.info(f"  - {job['title']} at {job['company']} in {job['location']}")
            else:
                logger.info("No jobs found matching the specific title/location keywords on the fake site.")

        except WebScraperError as e:
            logger.error(f"WebScraperError during fake site test: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during fake site test: {e}", exc_info=True)
    else:
        logger.warning("WebDriver test instance was not successfully created, so live scraping tests were skipped.")


    logger.info("\n--- Testing placeholder functions ---")
    search_jobs_linkedin("Software Engineer", "Remote")
    apply_for_job_on_site("https://example.com/job/123", {"name": "Test User"})

    logger.info("\n--- Web Scraper Standalone Test Complete ---")
