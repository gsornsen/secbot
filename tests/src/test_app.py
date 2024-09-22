from unittest import mock
from unittest.mock import AsyncMock, patch

import chainlit as cl
import pytest
from langchain.agents import AgentExecutor
from langchain.schema import LLMResult
from langchain.tools import Tool

from src.app import (
    ChainlitStreamingHandler,
    oauth_callback,
    on_chat_resume,
    process_chunk,
    setup_runnable,
    start_up,
)


@pytest.fixture
def mock_cl_user_session():
    with patch('src.app.cl.user_session') as mock_session:
        yield mock_session

@pytest.fixture
def mock_cl_Message():
    with patch('src.app.cl.Message') as mock_message:
        yield mock_message

@pytest.fixture
def mock_agent_executor():
    return AsyncMock(spec=AgentExecutor)

@pytest.mark.asyncio
async def test_ChainlitStreamingHandler():
    mock_message = AsyncMock()
    handler = ChainlitStreamingHandler(mock_message)

    await handler.on_llm_new_token("test token")
    mock_message.stream_token.assert_called_once_with("test token")

    await handler.on_llm_end(LLMResult(generations=[], llm_output=None))
    mock_message.update.assert_called_once()

def test_setup_runnable(mock_cl_user_session):
    setup_runnable()
    mock_cl_user_session.set.assert_any_call("runnable", mock.ANY)
    mock_cl_user_session.set.assert_any_call("memory", mock.ANY)

@pytest.mark.asyncio
async def test_oauth_callback():
    default_user = cl.User(identifier="test_user")
    result = await oauth_callback("provider", "token", {}, default_user)
    assert result == default_user

@pytest.mark.asyncio
async def test_start_up(mock_cl_user_session):
    await start_up()
    mock_cl_user_session.set.assert_called()

@pytest.mark.asyncio
async def test_on_chat_resume(mock_cl_user_session):
    thread = {
        "steps": [
            {"type": "user_message", "output": "user input"},
            {"type": "assistant_message", "output": "assistant response"},
        ]
    }
    await on_chat_resume(thread)
    mock_cl_user_session.set.assert_called()


@pytest.mark.asyncio
async def test_process_chunk():
    mock_msg = AsyncMock()

    # Test processing output chunk
    chunk = {"output": "test output"}
    await process_chunk(chunk, mock_msg)
    mock_msg.stream_token.assert_called_once_with("test output")

    # Test processing intermediate steps
    mock_msg.reset_mock()
    chunk = {
        "intermediate_steps": [
            (Tool(
                name="test_tool",
                func=lambda x: x,
                description="test"), "observation")
        ]
    }
    await process_chunk(chunk, mock_msg)
    # Called for action, observation, and thinking
    assert mock_msg.stream_token.call_count == 3

    # Test processing string chunk
    mock_msg.reset_mock()
    chunk = "test string"
    await process_chunk(chunk, mock_msg)
    mock_msg.stream_token.assert_called_once_with("test string")
