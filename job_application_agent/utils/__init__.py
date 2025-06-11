# This file marks utils as a Python package.
# It can also contain common utility functions.

import hashlib
import datetime
import re

def generate_unique_id(data_string: str) -> str:
    """
    Generates a SHA256 hash for a given string to produce a unique ID.

    Args:
        data_string (str): The input string to hash (e.g., a URL or concatenated details).

    Returns:
        str: A hexadecimal string representing the SHA256 hash.
    """
    if not isinstance(data_string, str):
        raise TypeError("Input 'data_string' must be a string.")

    sha256_hash = hashlib.sha256(data_string.encode('utf-8')).hexdigest()
    return sha256_hash

def format_datetime(dt_object: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formats a datetime object into a string.

    Args:
        dt_object (datetime.datetime): The datetime object to format.
        fmt (str, optional): The desired format string.
                             Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
        str: The formatted datetime string.
    """
    if not isinstance(dt_object, datetime.datetime):
        raise TypeError("Input 'dt_object' must be a datetime.datetime instance.")

    return dt_object.strftime(fmt)

def clean_text(text: str) -> str:
    """
    Performs basic text cleaning.
    - Removes leading/trailing whitespace.
    - Replaces multiple whitespace characters (including newlines, tabs) with a single space.
    - Can be extended for more specific cleaning tasks.

    Args:
        text (str): The input string to clean.

    Returns:
        str: The cleaned string.
    """
    if not isinstance(text, str):
        # Allow None to pass through, or raise TypeError if strictness is needed
        if text is None:
            return "" # Or return None, depending on desired behavior
        raise TypeError("Input 'text' must be a string.")

    # Replace multiple whitespace characters (including newlines, tabs, etc.) with a single space
    cleaned_text = re.sub(r'\s+', ' ', text)
    # Remove leading and trailing whitespace that might have been left or introduced
    cleaned_text = cleaned_text.strip()

    return cleaned_text

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    print("--- Utils Standalone Test ---")

    # Test generate_unique_id
    url1 = "https://example.com/job/123"
    url2 = "https://example.com/job/124"
    id1 = generate_unique_id(url1)
    id1_again = generate_unique_id(url1)
    id2 = generate_unique_id(url2)
    print(f"ID for '{url1}': {id1}")
    print(f"ID for '{url1}' (again): {id1_again}")
    print(f"ID for '{url2}': {id2}")
    assert id1 == id1_again
    assert id1 != id2
    assert len(id1) == 64 # SHA256 hex digest length

    try:
        generate_unique_id(123) # type: ignore
    except TypeError as e:
        print(f"Caught expected TypeError for generate_unique_id: {e}")

    # Test format_datetime
    now = datetime.datetime.now()
    formatted_now_default = format_datetime(now)
    formatted_now_custom = format_datetime(now, fmt="%d/%m/%Y %Hh%Mm")
    print(f"Current datetime (default format): {formatted_now_default}")
    print(f"Current datetime (custom format): {formatted_now_custom}")
    assert formatted_now_default == now.strftime("%Y-%m-%d %H:%M:%S")
    assert formatted_now_custom == now.strftime("%d/%m/%Y %Hh%Mm")

    try:
        format_datetime("not a datetime") # type: ignore
    except TypeError as e:
        print(f"Caught expected TypeError for format_datetime: {e}")

    # Test clean_text
    text1 = "  Hello   World  \n This is a test. \t Bye.  "
    cleaned1 = clean_text(text1)
    print(f"Original: '{text1}'\nCleaned1: '{cleaned1}'")
    assert cleaned1 == "Hello World This is a test. Bye."

    text2 = "NoExtraSpaces"
    cleaned2 = clean_text(text2)
    print(f"Original: '{text2}'\nCleaned2: '{cleaned2}'")
    assert cleaned2 == "NoExtraSpaces"

    text3 = "\n\n\t  Leading and trailing only \t\n"
    cleaned3 = clean_text(text3)
    print(f"Original: '{text3}'\nCleaned3: '{cleaned3}'")
    assert cleaned3 == "Leading and trailing only"

    text4 = ""
    cleaned4 = clean_text(text4)
    print(f"Original: '{text4}'\nCleaned4: '{cleaned4}'")
    assert cleaned4 == ""

    text5 = "   "
    cleaned5 = clean_text(text5)
    print(f"Original: '{text5}'\nCleaned5: '{cleaned5}'")
    assert cleaned5 == "" # Multiple spaces collapse to one, then strip makes it empty.

    text_none = None
    cleaned_none = clean_text(text_none) #type: ignore
    print(f"Original: {text_none}\nCleanedNone: '{cleaned_none}'")
    assert cleaned_none == ""


    print("\n--- Utils Standalone Test Complete ---")
