import os
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from dotenv import load_dotenv

load_dotenv(override=True)

def get_llm(temperature: float = 0):
    """
    Get the configured LLM instance.
    """
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    if not api_key:
        print("❌ No API Key found. Please set OPENAI_API_KEY or OPENROUTER_API_KEY.")
        return None
        
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=SecretStr(api_key),
        base_url=base_url
    )
