# src/app.py
import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# --- Load Environment Variables FIRST ---
load_dotenv() 

# --- Setup Database Path and Environment Variable SECOND ---
from utils.db_setup import setup_database
db_path = setup_database()
os.environ["DB_PATH"] = db_path 

# --- Import the rest of the app modules THIRD ---
from utils.vectorstore_setup import setup_vector_store
from assistants.graph import get_graph

st.set_page_config(page_title="Swiss Airlines Support Bot", layout="wide")

# --- API KEY CHECK ---
required_keys = ["GOOGLE_API_KEY", "GROQ_API_KEY", "TAVILY_API_KEY", "OPENAI_API_KEY"]
keys_loaded = all(os.getenv(key) for key in required_keys)

if not keys_loaded:
    st.error("API keys are not found. Please create a .env file in the project root and add all required keys.")
    st.code("""
    # .env file format:
    GOOGLE_API_KEY="your_key"
    GROQ_API_KEY="your_key"
    TAVILY_API_KEY="your_key"
    OPENAI_API_KEY="your_key"
    """)
    st.stop()

# --- Setup Utilities ---
vector_retriever = setup_vector_store()

@st.cache_resource
def load_graph():
    return get_graph()
graph = load_graph()

# --- Title and Session State ---
st.title("✈️ Swiss Airlines Support Assistant")
st.markdown("I can help with flight information, policy questions, and booking hotels, cars, or excursions.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# --- Display existing chat messages ---
for msg in st.session_state.messages:
    if isinstance(msg, AIMessage) and msg.tool_calls:
        if msg.content:
            with st.chat_message("ai"):
                st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("ai"):
            st.markdown(msg.content)
    elif isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)

# --- Main Interaction Logic ---
config = {"configurable": {"passenger_id": "3442 587242", "thread_id": st.session_state.thread_id}}

def process_and_display_response(user_input):
    st.session_state.messages.append(HumanMessage(content=user_input))
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("ai"):
        with st.spinner("Thinking..."):
            events = graph.stream({"messages": [("user", user_input)]}, config, stream_mode="values")
            full_response = None
            for event in events:
                if "messages" in event:
                    full_response = event["messages"][-1]
            if full_response and full_response.content:
                st.session_state.messages.append(full_response)
                st.markdown(full_response.content)

# Check if the agent is interrupted waiting for tool approval
snapshot = graph.get_state(config)
if snapshot.next:
    with st.chat_message("ai"):
        st.markdown("I need to perform the following actions. Do you approve?")
        for tool_call in snapshot.values['messages'][-1].tool_calls:
             st.code(f"Tool: {tool_call['name']}\nArguments: {tool_call['args']}", language="json")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve", use_container_width=True, key="approve_button"):
            with st.spinner("Continuing..."):
                events = graph.stream(None, config, stream_mode="values")
                final_response = None
                for event in events:
                    if "messages" in event:
                         final_response = event["messages"][-1]
                if final_response:
                    st.session_state.messages.append(final_response)
                st.rerun()

    with col2:
        if st.button("Deny", use_container_width=True, key="deny_button"):
            tool_call_id = snapshot.values['messages'][-1].tool_calls[0]['id']
            denial_message = ToolMessage(content="The user denied this tool call. Please ask for clarification.", tool_call_id=tool_call_id)
            with st.spinner("Re-routing..."):
                events = graph.stream({"messages": [denial_message]}, config, stream_mode="values")
                final_response = None
                for event in events:
                    if "messages" in event:
                         final_response = event["messages"][-1]
                if final_response:
                    st.session_state.messages.append(final_response)
                st.rerun()
else:
    # If not interrupted, show the chat input and demo buttons
    if prompt := st.chat_input("What can I help you with?"):
        st.session_state.demo_mode = False
        process_and_display_response(prompt)
        st.rerun()

    # Tutorial questions for the demo
    tutorial_questions = [
        "Hi there, what time is my flight?",
        "Am I allowed to update my flight to something sooner? I want to leave later today.",
        "Update my flight to sometime next week then",
        "The next available option is great",
        "What about lodging and transportation?",
        "Yeah I think I'd like an affordable hotel for my week-long stay (7 days). And I'll want to rent a car.",
        "OK could you place a reservation for your recommended hotel? It sounds nice.",
        "Yes go ahead and book anything that's moderate expense and has availability.",
        "Now for a car, what are my options?",
        "Awesome let's just get the cheapest option. Go ahead and book for 7 days",
        "Cool so now what recommendations do you have on excursions?",
        "Are they available while I'm there?",
        "Interesting - I like the museums, what options are there?",
        "OK great pick one and book it for my second day there.",
    ]

    # Initialize or manage demo state
    if "demo_step" not in st.session_state:
        st.session_state.demo_step = 0

    if st.button("Start Demo", key="start_demo"):
        # Reset chat and start demo from the beginning
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.demo_step = 0
        st.session_state.demo_mode = True
        st.rerun()

    if st.session_state.get("demo_mode"):
        step = st.session_state.demo_step
        if step < len(tutorial_questions):
            if st.button(f"Next Demo Step: '{tutorial_questions[step]}'", use_container_width=True, key=f"demo_step_{step}"):
                process_and_display_response(tutorial_questions[step])
                st.session_state.demo_step += 1
                st.rerun()
        else:
            st.info("🎉 Demo complete!")
            st.session_state.demo_mode = False
            st.session_state.demo_step = 0 # Reset for next time
            st.rerun()