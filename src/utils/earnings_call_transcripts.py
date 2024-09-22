import json
import ssl
from urllib.request import urlopen

import certifi

from utils.dcm import get_dcm_api_key

api_key = get_dcm_api_key()
base_api_url = "https://discountingcashflows.com"

async def get_available_transcripts(ticker: str) -> list:
    url = f"{base_api_url}/api/transcript/list/?ticker={ticker}&key={api_key}"

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urlopen(url, context=ssl_context) as response:
            data = json.loads(response.read().decode())
        return data
    except Exception as e:
        print(f"Error fetching available transcripts: {e}")
        return []

async def get_latest_transcript(ticker: str) -> dict:
    available_transcripts = await get_available_transcripts(ticker)
    if not available_transcripts:
        return {}

    latest = available_transcripts[0]
    quarter, year, _ = latest

    url = f"""
    {base_api_url}/api/transcript/?ticker={ticker}&quarter=Q{quarter}&year={year}&key={api_key}
    """

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urlopen(url, context=ssl_context) as response:
            data = json.loads(response.read().decode())
        return data[0] if data else {}
    except Exception as e:
        print(f"Error fetching latest transcript: {e}")
        return {}

async def get_specific_transcript(ticker: str, year: int, quarter: int) -> dict:
    """
    Fetches a specific earnings call transcript for a given company, year, and quarter.

    Args:
        ticker (str): The stock ticker symbol of the company.
        year (int): The year of the transcript.
        quarter (int): The quarter of the transcript (1-4).

    Returns:
        dict: The specific transcript data, including symbol,
        quarter, year, date, and content.
    """
    if quarter not in range(1, 5):
        raise ValueError("Quarter must be between 1 and 4")

    url = f"""
    {base_api_url}/api/transcript/?ticker={ticker}&quarter=Q{quarter}&year={year}&key={api_key}
    """

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urlopen(url, context=ssl_context) as response:
            data = json.loads(response.read().decode())
        return data[0] if data else {}
    except Exception as e:
        print(f"Error fetching specific transcript: {e}")
        return {}
