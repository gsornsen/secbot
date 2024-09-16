from typing import List

import chainlit as cl
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.memory import ConversationTokenBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from utils.edgar_reports import get_latest_report
from utils.openai import get_openai_api_key

OPEN_AI_KEY = get_openai_api_key()
MAX_TOKEN_LIMIT = 100000  # Increased to utilize more of GPT-4o's capacity


class TruncatedChatMessageHistory(ChatMessageHistory, BaseModel):
    truncate_at_tokens: int = Field(...)
    language_model: ChatOpenAI = Field(...)

    def get_messages(self) -> List[BaseMessage]:
        return self.truncate(list(super().messages))

    def truncate(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        total_tokens = 0
        truncated_messages = []

        for message in reversed(messages):
            tokens = self.language_model.get_num_tokens(message.content)
            if total_tokens + tokens > self.truncate_at_tokens:
                break
            total_tokens += tokens
            truncated_messages.append(message)

        return list(reversed(truncated_messages))


class AsyncConversationTokenBufferMemory(ConversationTokenBufferMemory):
    async def aget_messages(self):
        return self.chat_memory.messages

    async def aadd_messages(self, messages):
        for message in messages:
            self.chat_memory.add_message(message)


@tool
def get_company_report(company: str, report_type: str) -> str:
    """Returns a company's latest report

    Args:
        company: Company Stock Ticker
        report_type: Type of report eg: 10-Q, 10-K
    """
    full_report = get_latest_report(company, report_type)

    if full_report.startswith("Company"):
        return f"Error: {full_report} Please check the company ticker and try again."

    return full_report


def summarize_long_text(text: str, max_tokens: int = 10000) -> str:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=200,
        length_function=len,
    )
    texts = text_splitter.split_text(text)

    if len(texts) == 1:
        return texts[0]

    docs = [Document(page_content=t) for t in texts]
    chain = load_summarize_chain(model, chain_type="map_reduce")
    summary = chain.invoke(docs)
    return summary["output_text"]


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

sec_copilot_prompt = ChatPromptTemplate.from_messages(
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

model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=OPEN_AI_KEY)
memory = ConversationTokenBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    max_token_limit=MAX_TOKEN_LIMIT,
    llm=model,
    output_key="output",
)
tools = [get_company_report]
agent = create_tool_calling_agent(model, tools, sec_copilot_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    return_intermediate_steps=True,
    max_iterations=3,
)


@cl.on_chat_start
async def start_up():
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: AsyncConversationTokenBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=MAX_TOKEN_LIMIT,
            llm=model,
            output_key="output",
        ),
        input_messages_key="input",
        history_messages_key="chat_history",
        return_messages=True,
    )
    cl.user_session.set("chat_agent", agent_with_chat_history)
    cl.user_session.set("memory", memory)


@cl.on_message
async def query_llm(message: cl.Message):
    agent = cl.user_session.get("chat_agent")
    memory = cl.user_session.get("memory")
    msg = cl.Message(content="", author="Assistant")
    await msg.send()

    input_message = summarize_long_text(message.content, max_tokens=10000)
    chat_history = memory.chat_memory.messages

    if agent is None:
        raise ValueError("Agent is not initialized")

    async for chunk in agent.astream(
        {"input": input_message, "chat_history": chat_history},
        config={"configurable": {"session_id": cl.user_session.get("id")}},
    ):
        await process_chunk(chunk, msg)

    memory.save_context({"input": input_message}, {"output": msg.content})


async def process_chunk(chunk, msg):
    if chunk is None:
        return
    if isinstance(chunk, dict):
        if "output" in chunk:
            await msg.stream_token(chunk["output"])
        elif "intermediate_steps" in chunk:
            for step in chunk["intermediate_steps"]:
                if isinstance(step, tuple) and len(step) == 2:
                    action, observation = step
                    action_str = (
                        f"\nAction: {action.tool}\nInput: {action.tool_input}\n"
                    )
                    await msg.stream_token(action_str)
                    await msg.stream_token(f"Observation: {observation}\n")
    elif isinstance(chunk, str):
        await msg.stream_token(chunk)
