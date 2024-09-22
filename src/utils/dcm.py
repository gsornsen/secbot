import logging
import os

from dotenv import find_dotenv, load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_dcm_api_key():
    # Try to load environment variables from .env file
    load_dotenv(find_dotenv())

    # Try to get the API key using dotenv's get method
    api_key = os.getenv("DCM_API_KEY")

    if not api_key:
        logger.error("DCP_API_KEY not found or empty in .env file or OS environment.")
        raise ValueError(
            """
            DCM API key not found or empty.
            Please set a valid DCMP_API_KEY in your .env file
            or as an environment variable.
            """
        )

    logger.info("Successfully retrieved DCM API key.")
    return api_key
