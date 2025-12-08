import streamlit as st
import asyncio
import uuid
import json
from langchain_core.messages import HumanMessage
from agent.graph import app
from agent.state import AgentState

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SQL Analyst",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .stChatMessage {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #f7f7f8;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: transparent;
    }
    .stTextInput > div > div > input {
        border-radius: 24px;
        padding-left: 20px;
        border: 1px solid #e0e0e0;
    }
    /* Style for the Plan Card */
    div.plan-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [] 
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False
if "current_plan" not in st.session_state:
    st.session_state.current_plan = None

# --- HELPER FUNCTIONS ---

def map_reasoning_level(ui_selection):
    mapping = {"Fast": "low", "Think": "medium", "Deep Think": "high"}
    return mapping.get(ui_selection, "low")

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

async def stream_graph_events(initial_inputs, config):
    """
    Centralized function to run the graph, stream events to UI, 
    and collect logs for history.
    """
    status_container = st.status("Thinking...", expanded=True)
    thought_logs = [] 
    
    # NEW: Keep track of steps we've already seen to prevent duplicate logs
    logged_steps = set()
    
    try:
        async for event in app.astream(initial_inputs, config=config, stream_mode="values"):
            
            # 1. PLANNER NODE
            if "plan" in event and event["plan"]:
                if event.get("status") == "waiting_approval":
                    plan = event["plan"]
                    # Deduplicate: Only log if we haven't logged this specific plan object/id before
                    # (Simplified: logic assumes plan doesn't change repeatedly in one run)
                    if "Plan Generated" not in str(thought_logs): 
                        log_msg = f"🧠 **Planner:** Generated {len(plan.steps)} steps."
                        status_container.write(log_msg)
                        thought_logs.append(log_msg)
                        st.session_state.current_plan = plan

            # 2. EXECUTOR NODE
            if "results" in event and event["results"]:
                results = event["results"]
                # Get the latest step key (e.g., "step_1")
                last_key = list(results.keys())[-1]
                
                # --- FIX: CHECK IF ALREADY LOGGED ---
                if last_key not in logged_steps:
                    log_msg = f"⚙️ **Executor:** Finished {last_key}."
                    status_container.write(log_msg)
                    
                    # Preview data
                    data_preview = str(results[last_key])[:100] + "..."
                    status_container.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;`Output: {data_preview}`")
                    thought_logs.append(f"{log_msg} -> `{data_preview}`")
                    
                    # Mark as logged
                    logged_steps.add(last_key)

            # 3. ERROR HANDLER
            if event.get("error"):
                # Deduplicate errors if needed, or allow them if they persist
                err_msg = f"⚠️ **Error:** {event['error']}"
                if not thought_logs or thought_logs[-1] != err_msg:
                    status_container.error(err_msg)
                    thought_logs.append(err_msg)

        status_container.update(label="Processed", state="complete", expanded=False)
        return thought_logs

    except Exception as e:
        status_container.update(label="Error", state="error")
        st.error(f"System Error: {e}")
        return thought_logs
async def process_user_input(user_input: str, reasoning_level: str):
    """Step 1: New Question"""
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "current_step_index": 0,
        "retry_count": 0,
        "results": {},
        "error": None,
        "user_feedback": None,
        "plan": None,
        "status": "planning"
    }
    
    # Run Stream
    logs = await stream_graph_events(initial_state, config)
    
    # Check if we paused for approval or finished
    handle_post_run(config, logs)

async def resume_graph(user_text: str):
    """Step 2: Feedback/Approval"""
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    feedback_payload = user_text
    clean_text = user_text.strip().lower()
    if clean_text in ["yes", "y", "ok", "approve", "go", "proceed"]:
        feedback_payload = None 
    
    await app.aupdate_state(config, {"user_feedback": feedback_payload})
    
    # Resume Stream (passing None as we are resuming state)
    logs = await stream_graph_events(None, config)
    
    # Check if we paused or finished
    handle_post_run(config, logs)

def handle_post_run(config, current_logs):
    """Updates session state and history after a graph run"""
    snapshot = app.get_state(config)
    
    if snapshot.next:
        # Paused at Human Review
        st.session_state.awaiting_approval = True
    else:
        # Finished
        st.session_state.awaiting_approval = False
        st.session_state.current_plan = None
        
        # Get Final Answer
        if snapshot.values and "messages" in snapshot.values:
            last_msg = snapshot.values["messages"][-1]
            if isinstance(last_msg, str):
                # Append to history WITH thoughts
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": last_msg,
                    "thoughts": "\n\n".join(current_logs) # Store logs here
                })

# --- UI LAYOUT ---

col_title, col_settings = st.columns([3, 1], gap="large")
with col_title:
    st.markdown("### ⚡ SQL Analyst")
with col_settings:
    reasoning_mode = st.select_slider("Reasoning", options=["Fast", "Think", "Deep Think"], value="Think", label_visibility="collapsed")
st.markdown("---")

# 1. RENDER CHAT HISTORY (With Collapsible Thoughts)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # If there are saved thoughts, show them in an expander FIRST
        if "thoughts" in message and message["thoughts"]:
            with st.expander("💭 Process Details", expanded=False):
                st.markdown(message["thoughts"])
        
        st.markdown(message["content"])

# 2. PLAN CARD (Only when waiting for approval)
if st.session_state.awaiting_approval and st.session_state.current_plan:
    with st.chat_message("assistant"):
        st.markdown("I have created a plan. **Type 'yes' to execute** or **describe changes**.")
        
        plan = st.session_state.current_plan
        plan_html = f"🎯 Goal: {plan.final_objective}<hr>"
        for step in plan.steps:
            plan_html += f"<b>{step.step_id}.</b> {step.description} <code style='color:#666'>({step.tool_name})</code><br>"
        st.markdown(plan_html, unsafe_allow_html=True)

# 3. INPUT HANDLING
placeholder_text = "Ask a question about your data..."
if st.session_state.awaiting_approval:
    placeholder_text = "Type 'Yes' to approve, or explain what to change..."

if prompt := st.chat_input(placeholder_text):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent Response
    if st.session_state.awaiting_approval:
        with st.chat_message("assistant"):
            run_async(resume_graph(prompt))
        st.rerun()
    else:
        with st.chat_message("assistant"):
            backend_reasoning = map_reasoning_level(reasoning_mode)
            run_async(process_user_input(prompt, backend_reasoning))
        st.rerun()