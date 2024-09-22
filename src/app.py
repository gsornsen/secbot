from operator import itemgetter
from typing import Dict, Optional

import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.storage_clients import S3StorageClient
from chainlit.types import ThreadDict
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.agents.output_parsers.tools import ToolAgentAction
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import LLMResult
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

from utils.custom_data_layer import CustomSQLAlchemyDataLayer
from utils.earnings_call_transcripts import (
    get_latest_transcript,
    get_specific_transcript,
)
from utils.edgar_reports import get_latest_report
from utils.openai import get_openai_api_key
from utils.sqlite_data_layer import SQLiteDataLayer

open_ai_key = get_openai_api_key()
load_dotenv()

sqlite_data_layer = SQLiteDataLayer()

storage_client = S3StorageClient(
    bucket="chainlit",
)

data_layer = CustomSQLAlchemyDataLayer(
    conninfo="sqlite+aiosqlite:///data.db",
    storage_provider=storage_client,
)

cl_data._data_layer = data_layer


async def get_company_report(input_string: str):
    """
    Returns a company's latest report.
    Input should be in the format 'TICKER,REPORT_TYPE'
    """
    company, report_type = input_string.split(",")
    return await get_latest_report(company, report_type)

async def get_earnings_call_transcript(input_string: str):
    """
    Returns a company's earnings call transcript.
    Input should be in one of the following formats:
    - 'TICKER' for the latest transcript
    - 'TICKER,YEAR,QUARTER' for a specific transcript
    """
    parts = input_string.split(',')
    ticker = parts[0].strip()

    if len(parts) == 1:
        return await get_latest_transcript(ticker)
    elif len(parts) == 3:
        try:
            year = int(parts[1].strip())
            quarter = int(parts[2].strip())
            return await get_specific_transcript(ticker, year, quarter)
        except ValueError:
            return "Invalid input format. Year and quarter must be integers."
    else:
        return """
        Invalid input format. Use 'TICKER' for latest or
        'TICKER,YEAR,QUARTER' for specific transcript.
        """


SEC_COPILOT_TEMPLATE = """
You are an assistant chatbot named "SEC Copilot". Your expertise is
fetching data from the SEC EDGAR database, fetching earnings call
transcripts, answering questions about
the data fetched, summarizing financial reports from companies,
summarizing earnings calls based on transcripts, as well as
helping identify strategies to build functionality within scope
of the user's application to help those companies tackle their
most impactful issues based on their summarized data. If a question
is not about SEC data, 10-K, 10-Q, earnings reports, or other
public company financial data, respond with, "I only specialize
in answering questions and providing insight on public company
financial and earnings data."
"""


class ChainlitStreamingHandler(BaseCallbackHandler):
    def __init__(self, chainlit_message):
        self.chainlit_message = chainlit_message
        self.content = ""

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        if token.strip() and token != "0":
            self.content += token
            await self.chainlit_message.stream_token(token)

    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        if self.content:
            self.chainlit_message.content = self.content.strip()
        await self.chainlit_message.update()


def setup_runnable():
    memory = cl.user_session.get("memory")
    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=open_ai_key,
        streaming=True,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SEC_COPILOT_TEMPLATE),
            MessagesPlaceholder(variable_name="history"),
            (
                "system",
                "Use the following chat history to answer questions "
                "if possible: {history}",
            ),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    tools = [
        Tool(
            name="get_company_report",
            func=lambda x: get_company_report(x),
            coroutine=get_company_report,
            description="""
                Returns a company's latest report.
                Input should be a string in the format:
                'TICKER,REPORT_TYPE' (e.g., 'AAPL,10-K' or 'GOOGL,10-Q')
            """,
        ),
        Tool(
            name="get_earnings_call_transcript",
            func=lambda x: get_earnings_call_transcript(x),
            coroutine=get_earnings_call_transcript,
            description="""
                Returns a company's earnings call transcript.
                Input should be in one of the following formats:
                - 'TICKER' for the latest transcript
                - 'TICKER,YEAR,QUARTER' for a specific transcript
                (e.g., 'AAPL,2024,1' for the first quarter of 2024)
                (e.g., 'AAPL' for the latest transcript)
            """,
        )
    ]
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="history",
        output_key="output",
    )

    agent = create_openai_tools_agent(model, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        return_intermediate_steps=True,
    )

    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | agent_executor
    )

    cl.user_session.set("runnable", runnable)
    cl.user_session.set("memory", memory)


@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


@cl.on_chat_start
async def start_up():
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    setup_runnable()


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    try:
        memory = ConversationBufferMemory(return_messages=True)
        all_messages = thread["steps"]
        for message in all_messages:
            content = message.get("output", "").strip()
            if content:
                if message["type"] == "user_message":
                    memory.chat_memory.add_user_message(content)
                elif message["type"] == "assistant_message":
                    memory.chat_memory.add_ai_message(content)

        cl.user_session.set("memory", memory)
        cl.user_session.set("metadata", {})
        setup_runnable()
    except Exception as e:
        print(f"Error in on_chat_resume: {e}")


@cl.on_message
async def query_llm(message: cl.Message):
    memory = cl.user_session.get("memory")
    runnable = cl.user_session.get("runnable")

    msg = cl.Message(content="")
    await msg.send()

    streaming_handler = ChainlitStreamingHandler(msg)

    full_response = ""
    async for chunk in runnable.astream(
        {"input": message.content},
        config={"callbacks": [streaming_handler]},
    ):
        await process_chunk(chunk, msg)
        if isinstance(chunk, dict) and "output" in chunk:
            full_response += chunk["output"]
        elif isinstance(chunk, str):
            full_response += chunk

    # Remove duplicate responses
    full_response = full_response.strip()
    if full_response:
        if full_response.count(full_response.split()[0]) > 1:
            full_response = full_response.split(full_response.split()[0])[0]

    # Store the complete assistant response in the memory
    if full_response:
        memory.chat_memory.add_user_message(message.content)
        memory.chat_memory.add_ai_message(full_response)

    # Update the final assistant response in the UI
    if full_response:
        msg.content = full_response
        await msg.update()


async def process_chunk(chunk, msg):
    if isinstance(chunk, dict):
        if "output" in chunk:
            output = chunk["output"].strip()
            if output and output != "0":
                await msg.stream_token(output)
        elif "intermediate_steps" in chunk:
            for step in chunk["intermediate_steps"]:
                if isinstance(step, tuple) and len(step) == 2:
                    action, observation = step
                    if isinstance(action, ToolAgentAction):
                        action_str = f"""
                        \n🛠️ Tool Call: {action.tool}\n
                        Input: {action.tool_input}\n
                        """
                        await msg.stream_token(action_str)
                        await msg.stream_token("⏳ Executing tool...\n")
                        await msg.stream_token(f"📊 Observation: {observation}\n")
                    else:
                        await msg.stream_token(f"\n🛠️ Action: {action}\n")
                        await msg.stream_token(f"📊 Observation: {observation}\n")
                    await msg.stream_token("🤔 Thinking...\n")
    elif isinstance(chunk, str) and chunk.strip() and chunk != "0":
        await msg.stream_token(chunk)
    await msg.update()
