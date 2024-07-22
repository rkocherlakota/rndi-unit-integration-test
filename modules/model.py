import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

def set_credentials() -> str:
    load_dotenv()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return anthropic_api_key, openai_api_key

# Set credentials
ChatAnthropic.api_key = set_credentials()

# Initializing the model
claude_model = ChatAnthropic(model_name="claude-3-haiku-20240307", max_tokens=4096)
openai_model = ChatOpenAI(model_name = "gpt-4-turbo", temperature=0)