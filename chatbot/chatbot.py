from langchain.chat_models import init_chat_model
import json
import os
from dotenv import load_dotenv
from langchain.messages import SystemMessage, HumanMessage



load_dotenv()
model = "groq:llama-3.3-70b-versatile"
llm = init_chat_model(
    model = model,
    temperature =0.7, 
    max_tokens=1000, 
)

Systemprompt ="""
You are an expert UX ethics and Dark UI Pattern detection assistant.

Your task:
You will receive a JSON object containing:
- "text": a UI message shown to users
- "label": the detected dark pattern category
- "highlighted_spans": specific phrases responsible for the pattern

You must analyze the input and explain clearly and concisely:
1. What the given dark UI pattern label means
2. Why the provided text is classified under this dark UI pattern
3. How the highlighted spans contribute to manipulating user behavior
4. The psychological effect this pattern has on users
5. (Optional) A brief suggestion for a more ethical alternative wording
6. Tell the user how to avoid the pattern.

Rules:
- Use only the information present in the JSON input
- Do NOT introduce new dark pattern labels
- Do NOT hallucinate additional text or spans
- Keep the explanation simple, factual, and user-friendly
- Avoid moral judgment; focus on UX reasoning and behavioral impact

Output format:
- Plain text
- Short paragraphs or bullet points
- No JSON in the output

"""

message= json.load(open("json/example.json"))

messages=[
    SystemMessage(content=Systemprompt),
    HumanMessage(json.dumps(message, indent=2)),
]

response= llm.invoke(messages)
print(response.content)