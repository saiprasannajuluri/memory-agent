import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from hindsight_client import Hindsight
from openai import OpenAI

load_dotenv()

# ---- Connections ----
hs = Hindsight(base_url=os.getenv("HINDSIGHT_URL"), api_key=os.getenv("HINDSIGHT_API_KEY"))
llm = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
MODEL = "openai/gpt-oss-120b"

# ---- The job description for the brain ----
SYSTEM_PROMPT = """You are a smart loan-recovery assistant for field agents in India.
You will get MEMORY (past notes about this borrower) and a QUESTION.
Use the memory: past promises, excuses, broken promises, what tone worked, best time to call.
Give short, practical advice in bullet points.
If memory is empty, say this is a new borrower and give a polite generic approach."""


# ---- Machine 1: read the diary ----
def get_memories(borrower_id, question):
    try:
        result = hs.recall(bank_id=borrower_id, query=question)
        notes = ["- " + m.text for m in result.results]
        if len(notes) == 0:
            return "No memory yet."
        return "\n".join(notes)
    except Exception as error:
        return "Memory not available right now."


# ---- Machine 2: ask the brain (with or without memory) ----
def ask_agent(borrower_id, question, use_memory=True):
    if use_memory:
        memory = get_memories(borrower_id, question)
    else:
        memory = "Memory is switched OFF."

    full_message = "MEMORY:\n" + memory + "\n\nQUESTION:\n" + question

    for attempt in range(3):          # try up to 3 times if Groq fails
        try:
            response = llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_message},
                ],
            )
            return response.choices[0].message.content, memory
        except Exception as error:
            print("Groq failed, trying again...", error)

    return "Sorry, the AI is busy. Please try again.", memory


# ---- Machine 3: write in the diary ----
def save_call(borrower_id, notes):
    now = datetime.now(timezone.utc).isoformat()
    hs.retain(bank_id=borrower_id, content=notes, context="collection call", timestamp=now)
    # Also save to the shared team diary so the agent learns across ALL borrowers
    hs.retain(bank_id="team-playbook", content=borrower_id + ": " + notes,
              context="collection call outcome", timestamp=now)


# ---- Machine 4: think over everything ----
def team_insights(question="Which recovery approaches worked best, and for which kind of borrower?"):
    answer = hs.reflect(bank_id="team-playbook", query=question)
    return getattr(answer, "text", str(answer))