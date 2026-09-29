# RecoverIQ — the loan-recovery agent that remembers every borrower

Loan recovery agents make 40–50 calls a day. Every call starts from zero: *Who is this? What did they promise last time? Did they keep it? What tone works with them?* The answers are buried in notes nobody re-reads.

**RecoverIQ** is an AI agent that remembers every borrower and learns from every call, using [Hindsight](https://github.com/vectorize-io/hindsight) agent memory.

- **Without memory:** "Be polite and ask when they can pay." (generic)
- **With memory:** "He broke 2 promises, only answers after 7 pm, a firm tone worked last time. Ask for a same-day UPI part-payment of ₹10,000." (personal)

▶️ **[Watch the 3-minute demo](https://youtu.be/EutEFHR-4qQ)**

<!-- Add screenshot: ![Memory off vs on](screenshots/memory-off-vs-on.png) -->

## Features

- **Brief me** — before a call, get advice with memory OFF vs ON side by side
- **Log a call** — saves the call to memory and automatically catches the promise date, amount and mood
- **Risk level** — High / Medium / Low per borrower, with promises made vs broken
- **Team brain** — the agent reflects on ALL calls, writes lessons into its own memory, and uses them in every future brief

## How Hindsight memory is used

| Hindsight operation | Where | What it does |
|---|---|---|
| `retain` | `save_call()` | Saves each call note into the borrower's bank **and** the shared `team-playbook` bank |
| `recall` | `ask_agent()` | Before a brief, finds the borrower's history + relevant team lessons |
| `reflect` | `learn_lessons()` | Reasons over every call in `team-playbook`, finds patterns |
| `retain` (again) | `learn_lessons()` | Saves those lessons into `team-lessons`, so future briefs use them — **the agent gets smarter over time** |

**Memory banks**

- `borrower-XXXX` — one bank per borrower (their full story, never mixed with others)
- `team-playbook` — every call from every borrower (raw experience)
- `team-lessons` — lessons the agent learned by reflecting (its growing expertise)

```
Agent asks  ->  recall (borrower bank + team-lessons)  ->  LLM (Groq)  ->  advice
Call logged ->  retain (borrower bank + team-playbook)
"Learn"     ->  reflect (team-playbook)  ->  retain (team-lessons)
```

## Tech stack

- [Hindsight Cloud](https://ui.hindsight.vectorize.io) — agent memory
- [Groq](https://groq.com) — LLM (`openai/gpt-oss-120b`)
- Python + Streamlit — UI

## How to run

```bash
git clone https://github.com/saiprasannajuluri/memory-agent.git
cd memory-agent
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```
GROQ_API_KEY=your_groq_key
HINDSIGHT_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_hindsight_key
```

Load the sample data (30 fictional borrowers, 157 calls) and start the app:

```bash
python seed.py
streamlit run app.py
```

## Edge cases handled

- New borrower with no memory → safe, polite first-call advice
- Groq fails → retries 3 times, then a friendly message
- Hindsight unavailable → agent still answers without memory
- Empty input → warning instead of a crash
- Borrowers never mix → one memory bank per borrower

## Data

All borrower data is **fictional**, generated for demonstration. No real customer data is used.

## Links

- Hindsight: https://github.com/vectorize-io/hindsight
- Hindsight docs: https://hindsight.vectorize.io
- Demo video: https://youtu.be/EutEFHR-4qQ
- Article: [Reflect, Then Retain: How My Hindsight Agent Writes Its Own Playbook](https://medium.com/@saiprasannajuluri/reflect-then-retain-how-my-hindsight-agent-writes-its-own-playbook-b9b021d9262b)
