import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm(model_name: str = "gpt-4o", temperature: float = 0.0) -> ChatOpenAI:
    """
    Initializes and returns a LangChain ChatOpenAI instance.
    """
    return ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )
