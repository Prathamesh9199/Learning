import streamlit as st
import asyncio
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from agent.graph import app

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Dual-Brain SQL Analyst",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Main Chat Styles */
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    
    /* Node Headers */
    .node-header { font-weight: bold; margin-top: 8px; margin-bottom: 4px; display: block; }
    .node-kg { color: #2e86c1; } /* Blue */
    .node-sql { color: #e67e22; } /* Orange */
    .node-exec { color: #27ae60; } /* Green */
    
    /* Log Entries */
    .log-step { margin-left: 15px; border-left: 2px solid #ddd; padding-left: 8px; font-size: 0.85em; color: #555; }
    .log-result { margin-left: 15px; font-family: monospace; color: #d63384; font-size: 0.8em; background: #fff0f6; padding: 2px 5px; border-radius: 4px; }
    
    /* Insights & Plans */
    .insight-box { background-color: #e8f6f3; border-left: 4px solid #1abc9c; padding: 8px; font-size: 0.9em; color: #0e6251; margin: 5px 0; }
    .plan-box { background-color: #fff8e1; border-left: 4px solid #ffb300; padding: 8px; font-size: 0.9em; font-family: monospace; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [] 
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# State to handle the "Pause/Resume" logic
if "waiting_for_approval" not in st.session_state:
    st.session_state.waiting_for_approval = False
if "temp_logs" not in st.session_state:
    st.session_state.temp_logs = []
if "logged_milestones" not in st.session_state:
    st.session_state.logged_milestones = set()

# --- ASYNC HELPER ---
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# --- MAIN AGENT RUNNER ---
async def run_agent_graph(user_input: str, is_resuming: bool = False):
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    # 1. SETUP INPUTS
    if not is_resuming:
        # START NEW QUERY
        st.session_state.temp_logs = []
        st.session_state.logged_milestones = set()
        
        initial_inputs = {
            "messages": [HumanMessage(content=user_input)],
            "phase": "business_analysis",
            "current_step_index": 0,
            "retry_count": 0,
            "status": "planning",
            "results": {},
            "kg_plan": None,
            "sql_plan": None,
            "business_context": None
        }
        stream_input = initial_inputs
        status_label = "🧠 Dual-Brain working..."
    else:
        # RESUMING AFTER APPROVAL
        if user_input.lower() in ["yes", "y", "ok", "approve", "confirm"]:
            # User Approved
            stream_input = None 
            status_label = "⚙️ Executing SQL Plan..."
        else:
            # User gave feedback
            app.update_state(config, {"user_feedback": user_input})
            stream_input = None 
            status_label = "🔄 Adjusting Plan..."

    # Create the Status Container
    status_container = st.status(status_label, expanded=True)
    
    # Render existing logs immediately (so they don't disappear during resume)
    for log_html in st.session_state.temp_logs:
        status_container.markdown(log_html, unsafe_allow_html=True)

    # 2. STREAM EXECUTION
    try:
        async for event in app.astream(stream_input, config=config, stream_mode="values"):
            
            # Helper to append logs to both UI and Session State
            def add_log(html):
                st.session_state.temp_logs.append(html)
                status_container.markdown(html, unsafe_allow_html=True)

            # --- NODE: KG PLANNER ---
            if event.get("kg_plan"):
                mid = "kg_plan_start"
                if mid not in st.session_state.logged_milestones:
                    steps = len(event["kg_plan"].steps)
                    add_log(f"<span class='node-header node-kg'>📘 Right Brain (Planning)</span>")
                    add_log(f"<div class='log-step'>Defining strategy: {steps} conceptual checks needed.</div>")
                    st.session_state.logged_milestones.add(mid)

            # --- NODE: KG EXECUTOR ---
            if event.get("results") and event.get("phase") == "business_analysis":
                results = event["results"]
                for key, val in results.items():
                    mid = f"kg_res_{key}"
                    if mid not in st.session_state.logged_milestones:
                        tool = val.get("tool", "Tool")
                        add_log(f"<div class='log-step'>Executed <b>{tool}</b></div>")
                        st.session_state.logged_milestones.add(mid)

            # --- NODE: CONTEXT REFINER ---
            if event.get("business_context"):
                mid = "context_done"
                if mid not in st.session_state.logged_milestones:
                    ctx = event["business_context"]
                    # Truncate for display
                    short_ctx = ctx[:120] + "..." if len(ctx) > 120 else ctx
                    add_log(f"<div class='insight-box'><b>🧠 Insight:</b> {short_ctx}</div>")
                    st.session_state.logged_milestones.add(mid)

            # --- NODE: SQL PLANNER ---
            if event.get("sql_plan"):
                mid = "sql_plan_done"
                if mid not in st.session_state.logged_milestones:
                    plan = event["sql_plan"]
                    add_log(f"<span class='node-header node-sql'>📙 Left Brain (SQL Planning)</span>")
                    
                    plan_html = "<div class='plan-box'><b>PROPOSED PLAN:</b><br>"
                    for s in plan.steps:
                        plan_html += f"<b>{s.step_id}. {s.tool}</b>: {s.description}<br>"
                    plan_html += "</div>"
                    
                    add_log(plan_html)
                    st.session_state.logged_milestones.add(mid)

            # --- NODE: SQL EXECUTOR ---
            if event.get("results") and event.get("phase") in ["data_analysis", "data_execution"]:
                results = event["results"]
                for key, val in results.items():
                    mid = f"sql_res_{key}"
                    if mid not in st.session_state.logged_milestones:
                        
                        add_log(f"<span class='node-header node-exec'>⚙️ Executor (Running Step {key.replace('step_', '')})</span>")
                        
                        if isinstance(val, list) and len(val) > 0:
                            row_count = len(val)
                            preview = str(val[0])
                            add_log(f"<div class='log-result'>✅ Success. Returned {row_count} rows.<br>Top row: {preview}</div>")
                        else:
                            add_log(f"<div class='log-result'>Result: {str(val)[:100]}...</div>")
                        
                        st.session_state.logged_milestones.add(mid)

        # 3. POST-STREAM CHECKS
        snapshot = app.get_state(config)
        
        # A. PAUSED (Human Review)
        if snapshot.next and ('human_review' in str(snapshot.created_at) or snapshot.next == ('sql_executor',)):
            
            # Update UI Status
            status_container.update(label="Waiting for Approval", state="running", expanded=True)
            st.session_state.waiting_for_approval = True
            
            # --- THE FIX: SAVE LOGS TO THE MESSAGE ---
            # We join the temp_logs and save them to 'thoughts'. 
            # This ensures they appear in the chat history even if st.status disappears.
            full_logs = "".join(st.session_state.temp_logs)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": "📋 **Plan Generated.** Please review the steps above.\n\nType **'yes'** to proceed, or explain changes.",
                "thoughts": full_logs  # <--- CRITICAL FIX
            })
            return

        # B. COMPLETED
        st.session_state.waiting_for_approval = False
        status_container.update(label="Analysis Complete", state="complete", expanded=False)
        
        # Get Final Answer
        if snapshot.values and "messages" in snapshot.values:
            last_msg = snapshot.values["messages"][-1]
            content = last_msg.content if isinstance(last_msg, AIMessage) else "Analysis finished."
            
            full_logs = "".join(st.session_state.temp_logs)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": content,
                "thoughts": full_logs
            })

    except Exception as e:
        status_container.update(label="System Error", state="error")
        st.error(f"Error: {e}")


# --- UI LAYOUT ---

st.title("🤖 Dual-Brain SQL Analyst")
st.markdown("---")

# 1. RENDER HISTORY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "thoughts" in msg and msg["thoughts"]:
            with st.expander("🔎 Analysis Logic", expanded=False):
                st.markdown(msg["thoughts"], unsafe_allow_html=True)
        st.markdown(msg["content"])

# 2. INPUT HANDLING
placeholder = "Ask about sales, profits..."
if st.session_state.waiting_for_approval:
    placeholder = "Type 'yes' to approve, or give feedback..."

if prompt := st.chat_input(placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        is_resuming = st.session_state.waiting_for_approval
        run_async(run_agent_graph(prompt, is_resuming))
    
    st.rerun()