import json
import os
import datetime
from typing import Dict, Any, List, Optional

# Assuming config.py is in the job_application_agent directory
try:
    from job_application_agent import config
except ImportError:
    import config # type: ignore

from job_application_agent.core_modules.error_handler import DataStorageError, get_logger

logger = get_logger(__name__)

# --- Path Configuration & Initialization ---
# Default to current directory if DATA_STORAGE_PATH is not in config or config is not loaded.
# This makes the module potentially runnable standalone for simple tests, though config should always be present.
_DEFAULT_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data') # Fallback if config is missing

_DATA_STORAGE_BASE_PATH = getattr(config, 'DATA_STORAGE_PATH', _DEFAULT_DATA_PATH)
if not _DATA_STORAGE_BASE_PATH.endswith('/'): # Ensure trailing slash for os.path.join
    _DATA_STORAGE_BASE_PATH += '/'

# Correctly join paths now, relative to the project root structure defined in config.
# config.DATA_STORAGE_PATH is expected to be like "job_application_agent/data/"
# So, User Data Dir would be "job_application_agent/data/user_profiles"
USER_DATA_DIR = os.path.join(_DATA_STORAGE_BASE_PATH, "user_profiles")
JOB_HISTORY_DIR = os.path.join(_DATA_STORAGE_BASE_PATH, "job_applications") # Changed from job_history for clarity

_initialized = False

def initialize_storage():
    """
    Creates necessary data storage directories if they don't exist.
    Should be called once at application startup.
    """
    global _initialized
    if _initialized:
        return

    dirs_to_create = [USER_DATA_DIR, JOB_HISTORY_DIR]
    for dir_path in dirs_to_create:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Successfully created directory: {dir_path}")
            else:
                logger.debug(f"Directory already exists: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}", exc_info=True)
            # This is a critical error for data storage.
            raise DataStorageError(f"Failed to create necessary storage directory {dir_path}: {e}")
    _initialized = True
    logger.info("Job manager storage initialized.")

# --- Private Helper Functions for JSON I/O ---
def _write_json(file_path: str, data: Dict[Any, Any]) -> None:
    """Writes dictionary data to a JSON file."""
    logger.debug(f"Writing JSON data to: {file_path}")
    try:
        # Ensure directory for the file exists
        dir_name = os.path.dirname(file_path)
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name) # Create if writing to a new user's dir for example
            except OSError as e:
                raise DataStorageError(f"Failed to create directory {dir_name} for file {file_path}: {e}")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.debug(f"Successfully wrote JSON data to: {file_path}")
    except IOError as e:
        logger.error(f"IOError writing JSON to {file_path}: {e}", exc_info=True)
        raise DataStorageError(f"Failed to write to file {file_path}: {e}")
    except TypeError as e: # e.g. if data is not serializable
        logger.error(f"TypeError, data not JSON serializable for {file_path}: {e}", exc_info=True)
        raise DataStorageError(f"Data is not JSON serializable for {file_path}: {e}")

def _read_json(file_path: str) -> Optional[Dict[Any, Any]]:
    """Reads dictionary data from a JSON file."""
    logger.debug(f"Reading JSON data from: {file_path}")
    if not os.path.exists(file_path):
        logger.warning(f"JSON file not found: {file_path}")
        return None # Or raise DataStorageError("File not found") depending on desired strictness

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully read JSON data from: {file_path}")
        return data
    except IOError as e:
        logger.error(f"IOError reading JSON from {file_path}: {e}", exc_info=True)
        raise DataStorageError(f"Failed to read file {file_path}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError for file {file_path}: {e}", exc_info=True)
        raise DataStorageError(f"Invalid JSON format in file {file_path}: {e}")

# --- User Profile Management ---
def store_user_profile(user_id: str, cv_analysis: Dict[str, Any], preferences: Dict[str, Any]) -> None:
    """
    Saves or updates a user's profile data (CV analysis, preferences).
    """
    if not _initialized: initialize_storage() # Ensure directories exist

    profile_data = {
        "user_id": user_id,
        "cv_analysis": cv_analysis,
        "preferences": preferences,
        "last_updated": datetime.datetime.now().isoformat()
    }
    file_path = os.path.join(USER_DATA_DIR, f"{user_id}_profile.json")

    _write_json(file_path, profile_data)
    logger.info(f"User profile for {user_id} stored/updated successfully at {file_path}.")

def load_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Loads a user's profile data. Returns None if profile not found.
    """
    if not _initialized: initialize_storage()

    file_path = os.path.join(USER_DATA_DIR, f"{user_id}_profile.json")
    profile_data = _read_json(file_path)
    if profile_data:
        logger.info(f"User profile for {user_id} loaded successfully from {file_path}.")
        return profile_data
    else:
        logger.info(f"No profile found for user {user_id} at {file_path}.")
        return None

# --- Job Application Tracking ---
def log_application(user_id: str, job_id: str, job_details: Dict[str, Any], status: str = "applied") -> None:
    """
    Logs a new job application for a user or updates an existing one if job_id matches.
    job_id should be a unique identifier for the job posting (e.g., URL or a hash of it).
    """
    if not _initialized: initialize_storage()

    history_file_path = os.path.join(JOB_HISTORY_DIR, f"{user_id}_job_applications.json")

    job_history = _read_json(history_file_path)
    if job_history is None or not isinstance(job_history, list): # If file doesn't exist or is malformed
        job_history = []

    application_entry = {
        "job_id": job_id,
        "details": job_details, # e.g., title, company, url
        "status": status,
        "applied_at": datetime.datetime.now().isoformat(),
        "last_updated_status_at": datetime.datetime.now().isoformat()
    }

    # Check if job_id already exists to update it, otherwise append
    found_existing = False
    for i, entry in enumerate(job_history):
        if entry.get("job_id") == job_id:
            # Preserve original applied_at, update other fields
            original_applied_at = entry.get("applied_at", application_entry["applied_at"])
            job_history[i] = application_entry
            job_history[i]["applied_at"] = original_applied_at # Keep original application date
            job_history[i]["last_updated_status_at"] = datetime.datetime.now().isoformat()
            found_existing = True
            logger.info(f"Updated existing application for job_id {job_id} for user {user_id}.")
            break

    if not found_existing:
        job_history.append(application_entry)
        logger.info(f"Logged new application for job_id {job_id} for user {user_id}.")

    _write_json(history_file_path, job_history) # Note: _write_json expects a dict, here job_history is a list
                                               # This needs adjustment in _write_json or here.
                                               # For now, let's wrap job_history in a dict for _write_json.
    _write_json(history_file_path, {"applications": job_history})


def update_application_status(user_id: str, job_id: str, new_status: str) -> bool:
    """
    Updates the status of a specific job application for a user.
    Returns True if successful, False if the job_id was not found.
    """
    if not _initialized: initialize_storage()

    history_file_path = os.path.join(JOB_HISTORY_DIR, f"{user_id}_job_applications.json")

    job_history_data = _read_json(history_file_path)
    if job_history_data is None or "applications" not in job_history_data or not isinstance(job_history_data["applications"], list):
        logger.warning(f"No job history found or format is incorrect for user {user_id} when trying to update status for job {job_id}.")
        return False

    job_history = job_history_data["applications"]
    updated = False
    for application in job_history:
        if application.get("job_id") == job_id:
            application["status"] = new_status
            application["last_updated_status_at"] = datetime.datetime.now().isoformat()
            updated = True
            logger.info(f"Updated status for job {job_id} to '{new_status}' for user {user_id}.")
            break

    if updated:
        _write_json(history_file_path, {"applications": job_history})
        return True
    else:
        logger.warning(f"Job ID {job_id} not found in history for user {user_id}. Could not update status.")
        return False

def get_user_job_history(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves the list of job applications for a user.
    Returns an empty list if no history is found.
    """
    if not _initialized: initialize_storage()

    history_file_path = os.path.join(JOB_HISTORY_DIR, f"{user_id}_job_applications.json")
    job_history_data = _read_json(history_file_path)

    if job_history_data and "applications" in job_history_data and isinstance(job_history_data["applications"], list):
        logger.info(f"Job history for user {user_id} loaded. Count: {len(job_history_data['applications'])}.")
        return job_history_data["applications"]
    else:
        logger.info(f"No job history found for user {user_id}.")
        return []

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    # Setup basic logging for testing this module standalone
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    logger.info("--- Job Manager Standalone Test ---")

    # Ensure storage is initialized (creates directories)
    try:
        initialize_storage()
        logger.info(f"Data storage base path: {_DATA_STORAGE_BASE_PATH}")
        logger.info(f"User profiles directory: {USER_DATA_DIR}")
        logger.info(f"Job applications directory: {JOB_HISTORY_DIR}")
    except DataStorageError as e:
        logger.critical(f"Failed to initialize storage for testing: {e}")
        exit(1) # Cannot proceed with tests if storage can't be initialized

    test_user_id = "test_user_123"

    # 1. Test User Profile
    logger.info(f"\n--- Testing User Profile for {test_user_id} ---")
    mock_cv_analysis = {"skills": ["Python", "AI"], "experience_years": 5}
    mock_preferences = {"roles": ["AI Engineer"], "location": "Remote"}

    store_user_profile(test_user_id, mock_cv_analysis, mock_preferences)
    loaded_profile = load_user_profile(test_user_id)

    if loaded_profile:
        assert loaded_profile["user_id"] == test_user_id
        assert loaded_profile["cv_analysis"]["skills"] == ["Python", "AI"]
        logger.info(f"Profile loaded successfully: {loaded_profile.get('last_updated')}")
    else:
        logger.error("Failed to load profile for testing.")

    # 2. Test Job Application Logging
    logger.info(f"\n--- Testing Job Application Logging for {test_user_id} ---")
    job1_details = {"title": "AI Developer", "company": "OpenAI", "url": "https://openai.com/careers/1"}
    job2_details = {"title": "Python Dev", "company": "Google", "url": "https://google.com/careers/2"}

    log_application(test_user_id, "openai_job1", job1_details, status="interested")
    log_application(test_user_id, "google_job2", job2_details, status="applied")

    # Log same job again to test update within log_application
    log_application(test_user_id, "openai_job1", {"title": "AI Developer (Senior)", "company": "OpenAI", "url": "https://openai.com/careers/1"}, status="applied_via_agent")


    # 3. Test Get Job History
    logger.info(f"\n--- Testing Get Job History for {test_user_id} ---")
    history = get_user_job_history(test_user_id)
    if history:
        logger.info(f"Found {len(history)} applications in history.")
        for app in history:
            logger.info(f"  Job: {app.get('job_id')}, Status: {app.get('status')}, Details: {app.get('details', {}).get('title')}")
        assert len(history) == 2 # Should be 2 unique job_ids
    else:
        logger.error("Failed to retrieve job history or history is empty.")

    # 4. Test Update Application Status
    logger.info(f"\n--- Testing Update Application Status for {test_user_id} ---")
    update_success = update_application_status(test_user_id, "google_job2", "interview_scheduled")
    if update_success:
        logger.info("Status updated successfully for google_job2.")
    else:
        logger.error("Failed to update status for google_job2.")

    update_fail = update_application_status(test_user_id, "nonexistent_job", "rejected")
    if not update_fail:
        logger.info("Correctly failed to update status for non-existent job.")
    else:
        logger.error("Incorrectly succeeded or failed to report failure for non-existent job update.")

    # Verify updated history
    logger.info(f"\n--- Verifying Updated Job History for {test_user_id} ---")
    updated_history = get_user_job_history(test_user_id)
    if updated_history:
        for app in updated_history:
            if app.get("job_id") == "google_job2":
                assert app.get("status") == "interview_scheduled"
                logger.info(f"  Verified status for google_job2: {app.get('status')}")
            if app.get("job_id") == "openai_job1":
                 assert app.get("status") == "applied_via_agent" # Check update from log_application
                 logger.info(f"  Verified status for openai_job1: {app.get('status')}")

    # 5. Test non-existent user profile and history
    logger.info(f"\n--- Testing Non-Existent User ---")
    non_existent_user_id = "ghost_user_000"
    ghost_profile = load_user_profile(non_existent_user_id)
    assert ghost_profile is None
    logger.info(f"Loading profile for '{non_existent_user_id}' correctly returned None: {ghost_profile is None}")

    ghost_history = get_user_job_history(non_existent_user_id)
    assert ghost_history == []
    logger.info(f"Loading job history for '{non_existent_user_id}' correctly returned empty list: {ghost_history == []}")


    logger.info("\n--- Job Manager Standalone Test Complete ---")
    logger.info(f"Please check the contents of the '{_DATA_STORAGE_BASE_PATH}' directory.")
