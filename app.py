import streamlit as st
from agent import Agent
from db import init_db

# Page config
st.set_page_config(
    page_title="TaskPilot",
    page_icon="🚀",
    layout="wide"
)

# Init DB once
init_db()

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "trace_events" not in st.session_state:
    st.session_state.trace_events = []

# Layout: chat on left, trace on right
col_chat, col_trace = st.columns([3, 2])

with col_chat:
    st.title("🚀 TaskPilot")
    st.caption("Your personal productivity agent")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input
    user_input = st.chat_input("Ask me to send emails, create tasks, set reminders...")

    if user_input:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Run agent
        with st.chat_message("assistant"):
            with st.spinner("Working..."):
                agent = Agent()
                response = agent.run(user_input)
                st.session_state.trace_events = agent.tracer.events

            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

with col_trace:
    st.subheader("🔍 Agent Trace")

    if not st.session_state.trace_events:
        st.info("Send a message to see the agent's thinking process.")
    else:
        for event in st.session_state.trace_events:
            t = event["type"]
            d = event["data"]

            if t == "tool_call":
                with st.expander(f"🔧 Tool Call: `{d['tool_name']}`", expanded=True):
                    st.json(d["input"])

            elif t == "tool_result":
                with st.expander(f"✅ Tool Result: `{d['tool_name']}`", expanded=False):
                    st.json(d["result"])

            elif t == "llm_thinking":
                with st.expander("🤖 Thinking", expanded=False):
                    st.write(d["text"])

            elif t == "validation_failed":
                st.error(f"⚠️ Validation: {d['reason']}")

            elif t == "final_response":
                with st.expander("🎯 Final Response", expanded=False):
                    st.write(d["text"])

            elif t == "error":
                st.error(f"❌ {d['message']}")