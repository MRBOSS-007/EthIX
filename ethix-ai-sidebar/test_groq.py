import os
import sys
from dotenv import load_dotenv
import logging
import httpx

logging.basicConfig(level=logging.DEBUG)

print("Starting test...")

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

load_dotenv(dotenv_path="../.env")
key = os.getenv("GROQ_API_KEY")
print("Key length:", len(key) if key else 0)

llm = init_chat_model(
    model="groq:llama-3.3-70b-versatile",
    temperature=0.7, 
    max_tokens=1000, 
)

print("Invoking...")
messages = [SystemMessage(content="Hello"), HumanMessage(content="Hi")]
res = llm.invoke(messages)
print("Response:", res.content)
