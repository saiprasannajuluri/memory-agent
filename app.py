import json
import streamlit as st
from agent import ask_agent, save_call, team_insights

st.set_page_config(page_title="RecoverIQ", layout="wide")
st.title("RecoverIQ — the recovery agent that remembers every borrower")

# Load borrower list for the dropdown
with open("borrowers.json") as f:
    borrowers = json.load(f)
names = {b["id"]: b["name"] for b in borrowers}

# Left sidebar: pick a borrower
borrower = st.sidebar.selectbox("Pick a borrower", list(names.keys()),
                                format_func=lambda i: names[i] + " (" + i + ")")

tab1, tab2, tab3 = st.tabs(["Brief me", "Log a call", "Team insights"])

# ---- Tab 1: brief before a call, memory ON vs OFF side by side ----
with tab1:
    question = st.text_input("Question", "Brief me before my call. How should I approach them?")
    if st.button("Get brief"):
        left, right = st.columns(2)
        with left:
            st.subheader("Without memory")
            with st.spinner("Thinking..."):
                answer, _ = ask_agent(borrower, question, use_memory=False)
            st.write(answer)
        with right:
            st.subheader("With Hindsight memory")
            with st.spinner("Checking memory..."):
                answer, memory = ask_agent(borrower, question, use_memory=True)
            st.write(answer)
            with st.expander("What I remember"):
                st.text(memory)

# ---- Tab 2: log a new call ----
with tab2:
    notes = st.text_area("What happened on the call?")
    if st.button("Save to memory"):
        if notes.strip() == "":
            st.warning("Please write something first.")
        else:
            save_call(borrower, notes)
            st.success("Saved. The agent will remember this next time.")

# ---- Tab 3: patterns across all borrowers ----
with tab3:
    q = st.text_input("Ask about all borrowers",
                      "Which recovery approaches worked best, and for which kind of borrower?")
    if st.button("Find patterns"):
        with st.spinner("Reflecting on all calls..."):
            st.write(team_insights(q))