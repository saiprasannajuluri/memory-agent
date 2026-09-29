import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

llm = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
response = llm.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Answer in 2 lines."},
        {"role": "user", "content": "How should I talk to a borrower who missed an EMI?"},
    ],
)

print(response.choices[0].message.content)