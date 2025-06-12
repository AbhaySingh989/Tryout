import google.generativeai as genai
from google.generativeai.types import GenerationConfig # For more specific generation settings
from google.api_core import exceptions as google_exceptions # For specific API errors

from job_application_agent import config
from job_application_agent.core_modules.error_handler import LLMInterfaceError, ConfigError, get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Global variable for the generative model
# It's good practice to initialize this once.
_model = None

def configure_genai_client():
    """
    Configures the Google Generative AI client with the API key from config.py
    and initializes the generative model.
    Should be called once at application startup.
    """
    global _model
    if _model:
        logger.info("Gemini client already configured.")
        return

    try:
        api_key = getattr(config, 'GEMINI_API_KEY', None)
        if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
            logger.error("GEMINI_API_KEY not found or not set in config.py.")
            raise ConfigError("GEMINI_API_KEY is missing or not set in the configuration.")

        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel('gemini-1.5-flash-latest') # Using the specified model
        logger.info("Google Generative AI client configured successfully with gemini-1.5-flash-latest.")

    except ConfigError as e:
        # Re-raise ConfigError to be caught by the main application setup
        raise e
    except Exception as e:
        # Catch any other unexpected errors during configuration (e.g., issues with genai library itself)
        logger.error(f"Failed to configure Google Generative AI client: {e}", exc_info=True)
        raise LLMInterfaceError(f"An unexpected error occurred during Gemini client configuration: {e}")


async def _send_prompt_async(prompt_text: str, generation_config_override: GenerationConfig = None) -> str:
    """
    Sends a prompt to the configured Gemini model and returns the response text.
    This is an asynchronous version.

    Args:
        prompt_text (str): The text of the prompt to send to the model.
        generation_config_override (GenerationConfig, optional): Specific generation settings
            to override the model's default.

    Returns:
        str: The text part of the model's response.

    Raises:
        LLMInterfaceError: If the model is not configured, or if there's an API error,
                           or if the response is blocked or doesn't contain text.
    """
    if not _model:
        logger.error("Gemini model not configured. Call configure_genai_client() first.")
        raise LLMInterfaceError("Gemini model is not configured.")

    logger.debug(f"Sending prompt to Gemini: '{prompt_text[:100]}...'") # Log a snippet

    try:
        # Using generate_content_async for non-blocking calls
        response = await _model.generate_content_async(
            prompt_text,
            generation_config=generation_config_override
            # safety_settings=... # Consider adding safety settings if needed
        )

        # Accessing the text directly if available, otherwise checking parts.
        # Based on Gemini API, response.text should be the primary way for simple text.
        # response.parts might contain more complex data structures if the prompt requested it (e.g. function calls)
        # For simple text generation, response.text should be sufficient.

        if response.candidates:
            # Iterate through candidates (usually one for basic prompts)
            # Check for finish_reason
            for candidate in response.candidates:
                if candidate.finish_reason == 'STOP' and candidate.content and candidate.content.parts:
                    full_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    if full_text:
                        logger.debug(f"Gemini response received successfully. Length: {len(full_text)}")
                        return full_text
                elif candidate.finish_reason == 'MAX_TOKENS':
                    logger.warning("Gemini response truncated due to MAX_TOKENS.")
                    # Return truncated text if available
                    full_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    if full_text: return full_text
                elif candidate.finish_reason in ['SAFETY', 'RECITATION']:
                    logger.error(f"Gemini response blocked due to: {candidate.finish_reason}")
                    # Log safety ratings if available
                    if candidate.safety_ratings:
                        for rating in candidate.safety_ratings:
                            logger.error(f"Safety Rating: Category={rating.category}, Probability={rating.probability}")
                    raise LLMInterfaceError(f"Gemini prompt blocked due to {candidate.finish_reason}.")
                else: # Other finish reasons like 'OTHER' or 'UNSPECIFIED'
                    logger.error(f"Gemini generation stopped due to an unexpected reason: {candidate.finish_reason}")
                    raise LLMInterfaceError(f"Gemini generation failed with reason: {candidate.finish_reason}")

        # Fallback if response.text is not directly available or if candidates structure is different than expected
        if hasattr(response, 'text') and response.text:
            logger.debug(f"Gemini response received (via .text attribute). Length: {len(response.text)}")
            return response.text

        logger.error(f"No valid text content found in Gemini response. Response: {response}")
        raise LLMInterfaceError("No valid text content received from Gemini.")

    except google_exceptions.GoogleAPIError as e:
        logger.error(f"Gemini API error: {e}", exc_info=True)
        raise LLMInterfaceError(f"Gemini API error: {e}")
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred while sending prompt to Gemini: {e}", exc_info=True)
        raise LLMInterfaceError(f"Unexpected error interacting with Gemini: {e}")


# --- Core LLM Interaction Functions (Async stubs) ---

async def analyze_cv_text(cv_text: str) -> dict:
    """
    Analyzes raw CV text to extract structured information like skills, experience, etc.
    (This is an async function)
    """
    if not _model: configure_genai_client() # Ensure client is configured

    prompt = f"""
    Analyze the following CV text and extract key information.
    Return the information as a JSON object with the following keys:
    "contact_info": {{ "name": "...", "email": "...", "phone": "..." }},
    "summary": "...",
    "skills": ["skill1", "skill2", ...],
    "experience": [
        {{ "title": "...", "company": "...", "duration": "...", "responsibilities": ["...", "..."] }},
        ...
    ],
    "education": [
        {{ "degree": "...", "institution": "...", "year": "..." }},
        ...
    ]
    If some information is not available, use null or an empty list/string as appropriate.

    CV Text:
    ---
    {cv_text}
    ---

    JSON Output:
    """
    logger.info(f"Analyzing CV text (first 100 chars): {cv_text[:100]}...")
    try:
        response_text = await _send_prompt_async(prompt)
        # Basic parsing attempt, can be made more robust
        import json
        analysis = json.loads(response_text)
        logger.info("CV analysis successful.")
        logger.debug(f"CV Analysis result: {analysis}")
        return analysis
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM for CV analysis: {e}. Response text: {response_text[:500]}", exc_info=True)
        raise LLMInterfaceError(f"LLM response for CV analysis was not valid JSON: {e}")
    except LLMInterfaceError: # Re-raise specific LLM errors
        raise
    except Exception as e: # Catch-all for other unexpected errors during this function's execution
        logger.error(f"Unexpected error in analyze_cv_text: {e}", exc_info=True)
        raise LLMInterfaceError(f"Unexpected error during CV analysis: {e}")


async def generate_clarification_questions(cv_analysis: dict) -> list[str]:
    """
    Generates targeted questions based on CV analysis to clarify job preferences.
    (This is an async function)
    """
    if not _model: configure_genai_client()

    prompt = f"""
    Based on the following CV analysis, generate up to 11 targeted questions for the user
    to clarify their job preferences. The questions should help understand their desired roles,
    key skills they want to use, preferred work environment, salary expectations (ask sensitively, e.g., "What are your salary expectations, if you're comfortable sharing?"),
    location preferences (including remote work), and any other factors important for a job search.
    Return the questions as a JSON list of strings.

    CV Analysis:
    ---
    {cv_analysis}
    ---

    Example format: ["What are your top 3 desired job titles?", "Are you looking for remote, hybrid, or on-site roles?"]

    JSON List of Questions:
    """
    logger.info("Generating clarification questions based on CV analysis...")
    try:
        response_text = await _send_prompt_async(prompt)
        import json
        questions = json.loads(response_text)
        if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
            logger.error(f"LLM response for clarification questions is not a list of strings. Response: {questions}")
            raise LLMInterfaceError("LLM response for clarification questions was not a list of strings.")
        logger.info(f"Successfully generated {len(questions)} clarification questions.")
        logger.debug(f"Generated questions: {questions}")
        return questions
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM for questions: {e}. Response text: {response_text[:500]}", exc_info=True)
        raise LLMInterfaceError(f"LLM response for clarification questions was not valid JSON: {e}")
    except LLMInterfaceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_clarification_questions: {e}", exc_info=True)
        raise LLMInterfaceError(f"Unexpected error during question generation: {e}")

async def generate_cover_letter_snippet(cv_analysis: dict, job_description: str, user_preferences: dict) -> str:
    """
    Generates a concise, relevant snippet for a cover letter or application question.
    (This is an async function)
    """
    if not _model: configure_genai_client()

    prompt = f"""
    Given the user's CV analysis, their preferences, and the job description below,
    generate a concise and compelling snippet (2-3 sentences) that can be used in a cover letter
    or as an answer to a common application question (e.g., "Why are you interested in this role?").
    The snippet should highlight the most relevant skills and experiences from the CV
    that match the job description and align with user preferences.

    CV Analysis:
    ---
    {cv_analysis}
    ---

    User Preferences:
    ---
    {user_preferences}
    ---

    Job Description:
    ---
    {job_description}
    ---

    Cover Letter Snippet:
    """
    logger.info("Generating cover letter snippet...")
    try:
        snippet = await _send_prompt_async(prompt)
        logger.info("Cover letter snippet generated successfully.")
        logger.debug(f"Generated snippet: {snippet}")
        return snippet
    except LLMInterfaceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_cover_letter_snippet: {e}", exc_info=True)
        raise LLMInterfaceError(f"Unexpected error during cover letter snippet generation: {e}")


async def check_job_fit(cv_analysis: dict, job_description: str, user_preferences: dict) -> tuple[float, str]:
    """
    Assesses the fit between the user's profile and a job, returning a score and justification.
    (This is an async function)
    """
    if not _model: configure_genai_client()

    prompt = f"""
    Analyze the user's CV, their job preferences, and the provided job description.
    Assess the fit for the job.
    Return your assessment as a JSON object with two keys:
    1. "fit_score": A float between 0.0 (no fit) and 1.0 (perfect fit).
    2. "justification": A brief explanation (1-2 sentences) for the score, highlighting key matching factors or discrepancies.

    CV Analysis:
    ---
    {cv_analysis}
    ---

    User Preferences:
    ---
    {user_preferences}
    ---

    Job Description:
    ---
    {job_description}
    ---

    JSON Output (with "fit_score" and "justification"):
    """
    logger.info("Checking job fit...")
    try:
        response_text = await _send_prompt_async(prompt)
        import json
        assessment = json.loads(response_text)

        score = assessment.get("fit_score")
        justification = assessment.get("justification")

        if not isinstance(score, float) or not (0.0 <= score <= 1.0):
            logger.error(f"Invalid fit_score from LLM: {score}. Must be float between 0.0 and 1.0.")
            raise LLMInterfaceError("LLM returned an invalid fit_score.")
        if not isinstance(justification, str) or not justification.strip():
            logger.error(f"Missing or empty justification from LLM: {justification}")
            raise LLMInterfaceError("LLM returned an invalid or empty justification.")

        logger.info(f"Job fit assessment successful: Score={score}, Justification='{justification}'")
        return score, justification
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM for job fit: {e}. Response text: {response_text[:500]}", exc_info=True)
        raise LLMInterfaceError(f"LLM response for job fit assessment was not valid JSON: {e}")
    except LLMInterfaceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in check_job_fit: {e}", exc_info=True)
        raise LLMInterfaceError(f"Unexpected error during job fit assessment: {e}")

# Example Usage (for testing purposes, typically called from other modules or main.py)
if __name__ == '__main__':
    import asyncio

    async def main_test():
        print("--- llm_interface.py standalone test ---")
        # This test requires GEMINI_API_KEY to be correctly set in job_application_agent/config.py
        # For safety, this test will not run if config.py is not found or key is placeholder.
        try:
            configure_genai_client() # Call this first
            if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
                 print("GEMINI_API_KEY is not set in config. Skipping live API tests.")
                 return
        except ConfigError as e:
            print(f"Configuration error: {e}. Skipping live API tests.")
            return
        except LLMInterfaceError as e:
            print(f"LLM Interface error during setup: {e}. Skipping live API tests.")
            return


        mock_cv_text = """
        John Doe
        john.doe@email.com | (555) 123-4567

        Summary:
        Experienced Software Engineer with 5+ years in Python development,
        cloud computing (AWS), and API design. Proven ability to lead projects
        and deliver high-quality software solutions.

        Skills:
        Python, Java, C++, AWS, Docker, Kubernetes, REST APIs, SQL, NoSQL, Git

        Experience:
        Senior Software Engineer, Tech Solutions Inc. (Jan 2020 - Present)
        - Led a team of 5 engineers in developing a new cloud-based SaaS product.
        - Designed and implemented RESTful APIs for customer integrations.
        - Optimized database queries, improving performance by 30%.

        Software Engineer, Innovate Corp. (Jun 2017 - Dec 2019)
        - Developed and maintained backend services for a large-scale web application.
        - Contributed to CI/CD pipeline improvements.

        Education:
        Master of Science in Computer Science, University of Tech (2017)
        Bachelor of Science in Computer Engineering, State College (2015)
        """

        mock_job_description = """
        Job Title: Python Software Engineer (Cloud Focus)
        Company: Future Systems Ltd.
        Location: Remote

        We are seeking a skilled Python Software Engineer with experience in cloud technologies,
        particularly AWS. You will be responsible for designing, developing, and deploying
        backend services and APIs. Strong understanding of microservices architecture and
        containerization (Docker, Kubernetes) is a plus.
        """

        mock_user_preferences = {
            "desired_roles": ["Software Engineer", "Cloud Engineer"],
            "skills_to_use": ["Python", "AWS", "API Design"],
            "location": "Remote"
        }

        try:
            print("\n1. Testing CV Analysis...")
            cv_analysis_result = await analyze_cv_text(mock_cv_text)
            print(f"CV Analysis Result (snippet): Name: {cv_analysis_result.get('contact_info', {}).get('name')}, Skills: {cv_analysis_result.get('skills', [])[:3]}")

            if cv_analysis_result:
                print("\n2. Testing Clarification Question Generation...")
                questions_result = await generate_clarification_questions(cv_analysis_result)
                print(f"Generated Questions (first 3): {questions_result[:3]}")

                print("\n3. Testing Cover Letter Snippet Generation...")
                snippet_result = await generate_cover_letter_snippet(cv_analysis_result, mock_job_description, mock_user_preferences)
                print(f"Generated Snippet: {snippet_result}")

                print("\n4. Testing Job Fit Assessment...")
                fit_score, justification = await check_job_fit(cv_analysis_result, mock_job_description, mock_user_preferences)
                print(f"Job Fit: Score={fit_score}, Justification='{justification}'")

        except LLMInterfaceError as e:
            print(f"\nAn LLMInterfaceError occurred during testing: {e}")
        except ConfigError as e:
            print(f"\nA ConfigError occurred (ensure API key is set for live tests): {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")

        print("\n--- llm_interface.py standalone test complete ---")

    if __name__ == '__main__':
        # Setup an event loop to run the async main_test function
        try:
            asyncio.run(main_test())
        except RuntimeError as e: # Handle cases where asyncio.run might have issues (e.g. already running loop in some environments)
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                print("Test cannot run in this environment (possibly a notebook with an active event loop). Try running as a standalone script.")
            else:
                raise
