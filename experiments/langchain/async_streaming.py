import argparse
import os
import sys

from langchain_openai import ChatOpenAI

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.utils.openai import get_openai_api_key

open_ai_key = get_openai_api_key()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=open_ai_key,
    streaming=True,
    )

def main():
    parser = argparse.ArgumentParser(description="Async streaming with LangChain")
    parser.add_argument("prompt", type=str, help="The prompt to send to the LLM")
    args = parser.parse_args()

    for chunk in llm.stream([{"role": "user", "content": args.prompt}]):
        print(chunk.content, end="", flush=True)
    print()  # Add a newline at the end

if __name__ == "__main__":
    main()

