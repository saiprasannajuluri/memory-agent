"""
RecoverIQ agent - the brain + diary logic.

Memory design (Hindsight banks):
  borrower-XXXX   -> one diary per borrower (every call note)
  team-playbook   -> every call from every borrower (raw experience)
  team-lessons    -> short lessons the agent learned by REFLECTING on team-playbook
"""
import os
import re
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from hindsight_client import Hindsight
from openai import OpenAI

load_dotenv()

# ---- Connections ----
hs = Hindsight(base_url=os.getenv("HINDSIGHT_URL"), api_key=os.getenv("HINDSIGHT_API_KEY"))
llm = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
MODEL = "openai/gpt-oss-120b"

TEAM_BANK = "team-playbook"
LESSONS_BANK = "team-lessons"

SYSTEM_PROMPT = """You are RecoverIQ, a smart loan-recovery assistant for field agents in Hyderabad, India.
You get:
- BORROWER MEMORY: past notes about THIS borrower
- TEAM LESSONS: what worked across ALL borrowers
- a QUESTION from the agent
Rules:
- Use the memory: past promises, excuses, broken promises, what tone worked, best time to call.
- Use team lessons when this borrower matches a pattern.
- Answer in short bullet points: Situation, Best time to call, Tone to use, What to ask for, Watch out.
- If memory is empty, say this is a new borrower and give a polite, safe first-call approach.
- Never suggest threats, abuse or illegal recovery practices."""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _now():
    return datetime.now(timezone.utc).isoformat()


def _chat(system, user, tries=3):
    """Ask the LLM, retrying up to 3 times if Groq fails."""
    for attempt in range(tries):
        try:
            response = llm.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
            )
            return response.choices[0].message.content or ""
        except Exception as error:
            print("Groq failed, trying again...", error)
    return ""


def _parse_json(text):
    """Pull the first {...} block out of the LLM answer. Returns {} if it can't."""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group(0)) if match else {}
    except Exception:
        return {}


# ------------------------------------------------------------------
# Machine 1: read a diary
# ------------------------------------------------------------------
def get_memories(bank_id, question):
    try:
        result = hs.recall(bank_id=bank_id, query=question)
        notes = ["- " + m.text for m in result.results]
        return "\n".join(notes) if notes else "No memory yet."
    except Exception:
        return "No memory yet."


# ------------------------------------------------------------------
# Machine 2: ask the agent (memory ON or OFF)
# ------------------------------------------------------------------
def ask_agent(borrower_id, question, use_memory=True):
    if use_memory:
        memory = get_memories(borrower_id, question)
        lessons = get_memories(LESSONS_BANK, "recovery lessons: " + question + "\n" + memory[:500])
    else:
        memory = "Memory is switched OFF."
        lessons = "Memory is switched OFF."

    message = ("BORROWER MEMORY:\n" + memory +
               "\n\nTEAM LESSONS:\n" + lessons +
               "\n\nQUESTION:\n" + question)
    answer = _chat(SYSTEM_PROMPT, message)
    if not answer:
        answer = "Sorry, the AI is busy right now. Please try again in a minute."
    return answer, memory, lessons


# ------------------------------------------------------------------
# Machine 3: promise tracker + risk level for one borrower
# ------------------------------------------------------------------
def borrower_profile(borrower_id):
    memory = get_memories(borrower_id, "all promises made, whether they were kept, payments, mood, best time to call, what tone worked")
    if memory == "No memory yet.":
        return {"risk": "Unknown", "promises_made": 0, "promises_broken": 0,
                "best_time": "-", "best_tone": "-", "reason": "New borrower, no history yet."}

    prompt = """From these call notes, return ONLY a JSON object with keys:
"risk" ("Low", "Medium" or "High"),
"promises_made" (number), "promises_broken" (number),
"best_time" (short text), "best_tone" (short text),
"reason" (one sentence why this risk level).

CALL NOTES:
""" + memory
    data = _parse_json(_chat("You extract structured data from loan collection notes. Output JSON only.", prompt))
    return {
        "risk": data.get("risk", "Unknown"),
        "promises_made": data.get("promises_made", 0),
        "promises_broken": data.get("promises_broken", 0),
        "best_time": data.get("best_time", "-"),
        "best_tone": data.get("best_tone", "-"),
        "reason": data.get("reason", "Could not analyse right now."),
    }


# ------------------------------------------------------------------
# Machine 4: log a call (writes to 2 diaries + extracts the promise)
# ------------------------------------------------------------------
def save_call(borrower_id, notes):
    now = _now()
    hs.retain(bank_id=borrower_id, content=notes, context="collection call", timestamp=now)
    hs.retain(bank_id=TEAM_BANK, content=borrower_id + ": " + notes,
              context="collection call outcome", timestamp=now)

    # Pull out any promise so the agent can check it later
    prompt = """Read this collection call note. Return ONLY JSON with keys:
"promise_made" (true/false), "promise_date" (text or null), "amount" (number or null),
"mood" (one word), "outcome" (one short sentence).

NOTE: """ + notes
    return _parse_json(_chat("You extract structured data from loan collection notes. Output JSON only.", prompt))


# ------------------------------------------------------------------
# Machine 5: the LEARNING step
#   reflect over ALL calls -> write the lessons into the team-lessons diary
#   Next briefs recall these lessons, so the agent literally gets smarter.
# ------------------------------------------------------------------
def learn_lessons():
    question = ("Look at all collection calls. Write 5 short, specific lessons about which approach "
                "gets which type of borrower to pay (tone, timing, channel like WhatsApp, guarantor, "
                "partial payments). One lesson per line.")
    try:
        answer = hs.reflect(bank_id=TEAM_BANK, query=question)
        lessons = getattr(answer, "text", str(answer))
    except Exception as error:
        return "Could not learn right now: " + str(error)

    hs.retain(bank_id=LESSONS_BANK, content=lessons, context="learned recovery lessons", timestamp=_now())
    return lessons


def team_insights(question):
    try:
        answer = hs.reflect(bank_id=TEAM_BANK, query=question)
        return getattr(answer, "text", str(answer))
    except Exception as error:
        return "Could not reflect right now: " + str(error)
