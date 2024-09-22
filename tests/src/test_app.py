from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import process_chunk, summarize_long_text


@pytest.fixture
def mock_text_splitter():
    with patch("src.app.RecursiveCharacterTextSplitter") as mock:
        mock_instance = mock.return_value
        mock_instance.split_text.return_value = ["chunk1", "chunk2", "chunk3"]
        yield mock


@pytest.fixture
def mock_load_summarize_chain():
    with patch("src.app.load_summarize_chain") as mock:
        yield mock


@pytest.fixture
def mock_chat_openai():
    with patch("src.app.ChatOpenAI") as mock:
        yield mock


def test_summarize_long_text_short(mock_text_splitter):
    short_text = "This is a short text that doesn't need summarization."
    mock_text_splitter.return_value.split_text.return_value = [short_text]

    result = summarize_long_text(short_text)

    assert result == short_text
    mock_text_splitter.assert_called_once()
    mock_text_splitter.return_value.split_text.assert_called_once_with(short_text)


def test_summarize_long_text_long(
    mock_text_splitter, mock_load_summarize_chain, mock_chat_openai
):
    long_text = "This is a long text. " * 1000
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"output_text": "Summarized text"}
    mock_load_summarize_chain.return_value = mock_chain

    result = summarize_long_text(long_text)

    assert result == "Summarized text"
    mock_text_splitter.assert_called_once()
    mock_load_summarize_chain.assert_called_once()
    mock_chain.invoke.assert_called_once()


@pytest.mark.asyncio
async def test_process_chunk():
    mock_msg = AsyncMock()

    # Test processing a string chunk
    await process_chunk("String chunk", mock_msg)
    mock_msg.stream_token.assert_awaited_once_with("String chunk")

    # Test processing a dict chunk with output
    mock_msg.reset_mock()
    await process_chunk({"output": "Output chunk"}, mock_msg)
    mock_msg.stream_token.assert_awaited_once_with("Output chunk")

    # Test processing a dict chunk with intermediate steps
    mock_msg.reset_mock()
    chunk = {
        "intermediate_steps": [
            (MagicMock(tool="Test Tool", tool_input="Test Input"), "Test Observation")
        ]
    }
    await process_chunk(chunk, mock_msg)
    assert mock_msg.stream_token.await_count == 2
    mock_msg.stream_token.assert_any_await("\nAction: Test Tool\nInput: Test Input\n")
    mock_msg.stream_token.assert_any_await("Observation: Test Observation\n")


if __name__ == "__main__":
    pytest.main()
