import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import argparse

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from src.utils.openai import get_openai_api_key

open_ai_key = get_openai_api_key()

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
Question: {question}
Answer:
"""

sec_copilot_prompt_template = PromptTemplate(
    input_variables=["question"], template=sec_copilot_template
)

model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=open_ai_key)
chain = sec_copilot_prompt_template | model


async def query_llm(question):
    chunks = []
    async for chunk in chain.astream(question):
        chunks.append(chunk)
        print(chunk.content, end="", flush=True)
    print("\n")


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
