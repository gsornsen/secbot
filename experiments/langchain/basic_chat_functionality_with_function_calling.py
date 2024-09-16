import argparse
import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from experiments.edgar_playground import get_latest_report
from src.utils.openai import get_openai_api_key

open_ai_key = get_openai_api_key()


@tool
async def get_company_report(company: str, report_type: str) -> str:
    """Returns a company's latest report

    Args:
        company: Company Stock Ticker
        report_type: Type of report eg: 10-Q, 10-K
    """
    report = get_latest_report(company, report_type)
    return report


sec_copilot_template = """
You are an assistant chatbot named "SEC Copilot". Your expertise is
fetching data from the SEC EDGAR database, answering questions about
the data fetched, summarizing financial reports from companies,
summarizing earnings calls based on transcripts, as well as
helping identify strategies to build functionality within scope
of the user's application to help those companies tackle their
most impactful issues based on their summarized data. If a question
if not about SEC data, 10-K, 10-Q, earnings reports, or other
public company financial data, respond with, "I only specialize
in answering questions and providing insight on public company
financial and earnings data.
"""

sec_copilot_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", f"{sec_copilot_template}"),
        ("user", "{input}"),
        (
            "assistant",
            "Here's the current conversation and thought process:\n{agent_scratchpad}",
        ),
    ]
)

tools = [get_company_report]
model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=open_ai_key)
agent = create_tool_calling_agent(model, tools, sec_copilot_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


async def query_llm(question):
    async for chunk in agent_executor.astream({"input": question}):
        print(chunk, end="", flush=True)


async def main():
    parser = argparse.ArgumentParser(
        description="""
        SEC Copilot: An AI assistant for SEC EDGAR database queries and
        financial report analysis.
        """
    )
    parser.add_argument(
        "prompt", type=str, help="The question or prompt for the SEC Copilot"
    )
    args = parser.parse_args()

    await query_llm(args.prompt)


if __name__ == "__main__":
    asyncio.run(main())
