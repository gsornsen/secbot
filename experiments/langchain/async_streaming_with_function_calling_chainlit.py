import os
import random
import sys

import chainlit as cl
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.utils.openai import get_openai_api_key

open_ai_key = get_openai_api_key()


@tool
async def where_cat_is_hiding() -> str:
    """Where is the cat hiding right now?"""
    return random.choice(["under the bed", "on the shelf"])


@tool
async def get_items(place: str) -> str:
    """Use this tool to look up which items are in the given place."""
    if "bed" in place:  # For under the bed
        return "socks, shoes and dust bunnies"
    if "shelf" in place:  # For 'shelf'
        return "books, penciles and pictures"
    else:  # if the agent decides to ask about a different place
        return "cat snacks"


model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=open_ai_key,
    streaming=True,
)
prompt = hub.pull("hwchase17/openai-tools-agent")
tools = [get_items, where_cat_is_hiding]
agent = create_openai_tools_agent(
    model.with_config({"tags": ["agent_llm"]}), tools, prompt
)

agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
    {"run_name": "Agent"}
)


@cl.on_chat_start
async def start_up():
    cl.user_session.set("chat_agent", agent_executor)


@cl.on_message
async def query_llm(message: cl.Message):
    agent = cl.user_session.get("chat_agent")
    if agent is None:
        raise ValueError("Agent is not initialized")

    msg = cl.Message(content="", author="Assistant")
    await msg.send()

    async for event in agent.astream_events(
        {"input": message.content},
        version="v1",
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                await msg.stream_token(content)
