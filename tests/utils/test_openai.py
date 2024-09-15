import pytest

from src.utils.openai import get_openai_api_key


def test_get_openai_api_key_success(monkeypatch):
    # Mock the environment variable
    monkeypatch.setenv("OPEN_AI_TOKEN", "test_api_key")

    # Call the function
    api_key = get_openai_api_key()

    # Assert that the returned API key matches the mocked value
    assert api_key == "test_api_key"

def test_get_openai_api_key_missing(monkeypatch):
    # Ensure the environment variable is not set
    monkeypatch.delenv("OPEN_AI_TOKEN", raising=False)

    # Call the function and expect a ValueError
    with pytest.raises(ValueError) as excinfo:
        get_openai_api_key()

    # Check the error message
    assert "OpenAI API key not found" in str(excinfo.value)

def test_get_openai_api_key_empty(monkeypatch):
    # Set an empty API key
    monkeypatch.setenv("OPEN_AI_TOKEN", "")

    # Call the function and expect a ValueError
    with pytest.raises(ValueError) as excinfo:
        get_openai_api_key()

    # Check the error message
    assert "OpenAI API key not found" in str(excinfo.value)
