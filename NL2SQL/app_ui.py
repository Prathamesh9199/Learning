import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from db_agent.graph_builder import build_graph
from db_agent.graph.sql_checkpointer import SQLServerSaver 
from db_agent.client.az_sql import SQLQueryExecutor

# =============================================================================
# 1. THEME CONFIGURATION (Anthropic Light Inspired)
# =============================================================================
st.set_page_config(
    page_title="Sherlock",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS for Fonts and Colors
st.markdown("""
<style>
    /* Import Fonts: Source Serif Pro (Headings) and Inter (Body) */
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+Pro:wght@400;600&family=Inter:wght@300;400;500&display=swap');

    /* Global Reset */
    .stApp {
        background-color: #ffffff; /* Pure White Background */
        font-family: 'Inter', sans-serif;
        color: #333333;
    }

    /* Headings (Serif) */
    h1, h2, h3 {
        font-family: 'Source Serif Pro', serif;
        font-weight: 600;
        color: #1a1a1a;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #fbf9f6; /* Warm Off-White (Anthropic style) */
        border-right: 1px solid #e5e5e5;
    }
    
    /* Button Styling (Subtle) */
    .stButton button {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        color: #333;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        border-color: #b0b0b0;
        background-color: #f5f5f5;
    }

    /* Input Box styling */
    .stChatInputContainer textarea {
        font-family: 'Inter', sans-serif;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: transparent;
    }
    /* User Message Bubble */
    div[data-testid="stChatMessage"][data-test-role="user"] {
        background-color: #f4f4f3; /* Light warm gray */
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    /* Assistant Message - Clean */
    div[data-testid="stChatMessage"][data-test-role="assistant"] {
        background-color: transparent;
        padding-left: 0;
    }

    /* "Thinking" Accordion Styling */
    .stStatus {
        border: 1px solid #e5e5e5;
        background-color: #ffffff;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
    }
    
    /* Logs inside the accordion */
    .stCodeBlock {
        border: none;
        background-color: #f9f9f9 !important;
    }
    code {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. SESSION LOGIC (Sidebar)
# =============================================================================
def get_all_sessions():
    query = """
    IF OBJECT_ID('agent_checkpoints', 'U') IS NOT NULL
        SELECT DISTINCT thread_id FROM agent_checkpoints ORDER BY thread_id DESC
    ELSE
        SELECT '' AS thread_id WHERE 1=0
    """
    try:
        with SQLQueryExecutor() as executor:
            df = executor.execute_query(query)
            return df['thread_id'].tolist() if not df.empty else []
    except Exception:
        return [] 

def sidebar_logic():
    with st.sidebar:
        st.markdown("### 🕵️‍♂️ Sherlock Agent")
        st.caption("v2.1 | SQL Investigator")
        st.markdown("---")
        
        # New Session Button
        if st.button("＋ New Session", use_container_width=True):
            new_id = f"session_{int(datetime.now().timestamp())}"
            st.session_state.current_thread_id = new_id
            st.session_state.messages = [] 
            st.rerun()

        st.markdown("#### History")
        
        # Session List
        sessions = get_all_sessions()
        current = st.session_state.get("current_thread_id", "session_user_1")
        
        if current not in sessions:
            sessions.insert(0, current)
            
        # Radio button for session selection
        selected = st.radio(
            "Select Session",
            sessions,
            index=sessions.index(current) if current in sessions else 0,
            label_visibility="collapsed",
            key="session_radio"
        )
        
        if selected != st.session_state.current_thread_id:
            st.session_state.current_thread_id = selected
            st.session_state.messages = [] 
            st.rerun()

        st.markdown("---")
        with st.expander("Settings & Profile"):
            st.write(f"**Thread:** `{st.session_state.current_thread_id}`")
            if st.button("Reset Cache"):
                st.toast("Cache cleared.")

if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = "session_user_1"
if "messages" not in st.session_state:
    st.session_state.messages = []

sidebar_logic()

# =============================================================================
# 3. CHAT INTERFACE
# =============================================================================

# Header
st.markdown(f"### Session: {st.session_state.current_thread_id}")

# Helper to de-duplicate logs for display
def dedup_logs(log_list):
    seen = set()
    return [x for x in log_list if not (x in seen or seen.add(x))]

# Render History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # 1. Show Logs (Collapsed)
        if "logs" in msg and msg["logs"]:
            unique_logs = dedup_logs(msg["logs"])
            with st.status("Thinking Process", state="complete", expanded=False):
                st.code("\n".join(unique_logs), language="text")
        
        # 2. Show Content
        st.markdown(msg["content"])
        
        # 3. Show Data
        if "data" in msg and msg["data"]:
            st.dataframe(msg["data"], hide_index=True)

# =============================================================================
# 4. AGENT EXECUTION
# =============================================================================
async def run_agent(user_input):
    
    # Setup
    checkpointer = SQLServerSaver()
    workflow = build_graph()
    app = workflow.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": st.session_state.current_thread_id}}
    
    # 1. Render User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Render Assistant Response
    with st.chat_message("assistant"):
        # The "Glass Box" Container
        status_box = st.status("Thinking...", expanded=True)
        log_area = status_box.empty()
        answer_area = st.empty()
        
        logs_captured = []
        final_answer = ""
        final_data = None
        
        try:
            inputs = {"messages": [("user", user_input)]}

            config = {
                "configurable": {"thread_id": st.session_state.current_thread_id},
                "recursion_limit": 100  # <--- Set it HERE inside config
            }
            
            async for event in app.astream(inputs, config=config, stream_mode="values"):
                
                # --- LOG STREAMING ---
                if "stream_buffer" in event and event["stream_buffer"]:
                    raw_logs = event["stream_buffer"]
                    
                    # Deduplicate visuals for the user
                    unique_logs = dedup_logs(raw_logs)
                    
                    # Update Log Area
                    log_area.code("\n".join(unique_logs), language="text")
                    logs_captured = raw_logs # Keep raw for history

                # --- DATA STREAMING ---
                if "sql_result" in event and event["sql_result"]:
                    final_data = event["sql_result"]

                # --- ANSWER STREAMING ---
                if "messages" in event and len(event["messages"]) > 0:
                    last = event["messages"][-1]
                    if hasattr(last, "content") and last.type == "ai":
                         final_answer = last.content
                         answer_area.markdown(final_answer + " ▌") # Typing cursor effect

            # Finish
            status_box.update(label="Complete", state="complete", expanded=False)
            answer_area.markdown(final_answer) # Remove cursor
            
            if final_data:
                st.dataframe(final_data, hide_index=True)

            # Save to State
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_answer,
                "logs": logs_captured,
                "data": final_data
            })

        except Exception as e:
            status_box.update(label="Error", state="error")
            st.error(f"System Error: {e}")

# Input Handler
if prompt := st.chat_input("Ask a question..."):
    asyncio.run(run_agent(prompt))