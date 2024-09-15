import logging
import os

from dotenv import find_dotenv, load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("utils")


def get_openai_api_key():
    # Try to load environment variables from .env file
    load_dotenv(find_dotenv())

    # Try to get the API key using dotenv's get method
    api_key = os.getenv("OPEN_AI_TOKEN")

    if not api_key:
        logger.error("OPEN_AI_TOKEN not found or empty in .env file or OS environment.")
        raise ValueError(
            """
            OpenAI API key not found or empty.
            Please set a valid OPEN_AI_TOKEN in your .env file
            or as an environment variable.
            """
        )

    logger.info("Successfully retrieved OpenAI API key.")
    return api_key
