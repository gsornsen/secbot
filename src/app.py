from typing import Dict, Optional

import chainlit as cl
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationTokenBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from utils.edgar_reports import get_latest_report
from utils.openai import get_openai_api_key

open_ai_key = get_openai_api_key()
load_dotenv()


@tool
async def get_company_report(company: str, report_type: str):
    """Returns a company's latest report"""
    return await get_latest_report(company, report_type)


SEC_COPILOT_TEMPLATE = """
You are an assistant chatbot named "SEC Copilot". Your expertise is
fetching data from the SEC EDGAR database, answering questions about
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

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SEC_COPILOT_TEMPLATE),
        (
            "system",
            "Use the following chat history to answer questions "
            "if possible: {chat_history}",
        ),
        ("human", "{input}"),
        (
            "assistant",
            "Here's the current conversation and thought process:\n{agent_scratchpad}",
        ),
    ]
)


model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=open_ai_key,
    streaming=True,
)
tools = [get_company_report]
memory = ConversationTokenBufferMemory(
    llm=model,
    max_token_limit=100000,
    return_messages=True,
    memory_key="chat_history",
)
agent = create_openai_tools_agent(
    model.with_config({"tags": ["agent_llm"]}), tools, prompt
)

agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
    {"run_name": "Agent"}
)


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
    cl.user_session.set("chat_agent", agent_executor)
    cl.user_session.set("memory", memory)


@cl.on_message
async def query_llm(message: cl.Message):
    agent = cl.user_session.get("chat_agent")
    agent_memory = cl.user_session.get("memory")
    chat_history = agent_memory.chat_memory.messages

    if agent is None:
        raise ValueError("Agent is not initialized")

    msg = cl.Message(content="", author="Assistant")
    await msg.send()

    async for event in agent.astream_events(
        {"input": message.content, "chat_history": chat_history},
        version="v1",
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                await msg.stream_token(content)

    agent_memory.save_context({"input": message.content}, {"output": msg.content})
