import json
import streamlit as st
from agent import ask_agent, save_call, borrower_profile, learn_lessons, team_insights

st.set_page_config(page_title="RecoverIQ", page_icon="🧠", layout="wide")
st.title("RecoverIQ")
st.caption("The loan-recovery agent that remembers every borrower and learns from every call — powered by Hindsight memory")

# ---- Load borrowers ----
with open("borrowers.json", encoding="utf-8") as f:
    borrowers = json.load(f)
info = {b["id"]: b for b in borrowers}

# ---- Sidebar ----
borrower = st.sidebar.selectbox(
    "Pick a borrower", list(info.keys()),
    format_func=lambda i: info[i]["name"] + " (" + i + ")")
b = info[borrower]
st.sidebar.markdown(f"**{b['name']}**  \n{b['car']} · EMI Rs {b['emi']:,}  \n{b.get('area', '')}")
st.sidebar.markdown(f"Calls on record: **{len(b['calls'])}**")

if st.sidebar.button("Analyse borrower"):
    with st.spinner("Reading memory..."):
        st.session_state["profile_" + borrower] = borrower_profile(borrower)

profile = st.session_state.get("profile_" + borrower)
if profile:
    colour = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(profile["risk"], "⚪")
    st.sidebar.markdown(f"### Risk: {colour} {profile['risk']}")
    st.sidebar.markdown(
        f"- Promises made: **{profile['promises_made']}**\n"
        f"- Promises broken: **{profile['promises_broken']}**\n"
        f"- Best time: {profile['best_time']}\n"
        f"- Best tone: {profile['best_tone']}")
    st.sidebar.caption(profile["reason"])

tab1, tab2, tab3 = st.tabs(["Brief me", "Log a call", "Team brain"])

# ---- Tab 1: memory OFF vs ON ----
with tab1:
    question = st.text_input("Question", "Brief me before my call. How should I approach them?")
    if st.button("Get brief", type="primary"):
        if not question.strip():
            st.warning("Please type a question.")
        else:
            left, right = st.columns(2)
            with left:
                st.subheader("Without memory")
                with st.spinner("Thinking..."):
                    answer, _, _ = ask_agent(borrower, question, use_memory=False)
                st.write(answer)
            with right:
                st.subheader("With Hindsight memory")
                with st.spinner("Checking memory..."):
                    answer, memory, lessons = ask_agent(borrower, question, use_memory=True)
                st.write(answer)
                with st.expander("What I remember about this borrower"):
                    st.text(memory)
                with st.expander("Team lessons I used"):
                    st.text(lessons)

# ---- Tab 2: log a call, see the promise it caught ----
with tab2:
    notes = st.text_area("What happened on the call?",
                         placeholder="e.g. Said salary delayed, promised Rs 10,000 on 12th Oct, calm on phone, call after 7 pm")
    if st.button("Save to memory", type="primary"):
        if not notes.strip():
            st.warning("Please write something first.")
        else:
            with st.spinner("Saving and reading the call..."):
                extracted = save_call(borrower, notes)
            st.success("Saved. The agent will remember this next time.")
            if extracted:
                st.markdown("**What the agent caught from this call:**")
                st.json(extracted)
            st.session_state.pop("profile_" + borrower, None)  # risk must be recalculated

# ---- Tab 3: the agent learns across ALL borrowers ----
with tab3:
    st.markdown("**Step 1 — Learn:** the agent reflects on every call and saves the lessons into its memory. "
                "From then on, every brief uses these lessons.")
    if st.button("Learn from all calls", type="primary"):
        with st.spinner("Reflecting on all calls..."):
            st.write(learn_lessons())
        st.success("Lessons saved to the team-lessons memory.")

    st.divider()
    st.markdown("**Step 2 — Ask anything about all borrowers:**")
    q = st.text_input("Question", "Which borrowers are most likely to break their next promise, and why?")
    if st.button("Ask the team brain"):
        with st.spinner("Reflecting..."):
            st.write(team_insights(q))
