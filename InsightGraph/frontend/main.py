import gradio as gr
import sys
from pathlib import Path
import time
import threading

# Add parent directory to path to import agent module
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import graph, logger

def format_event(event):
    """Format a logger event into readable text"""
    event_type = event.get('type', 'unknown')
    payload = event.get('payload', {})
    
    if event_type == 'thought':
        return f"💭 {payload.get('thought', '')}"
    elif event_type == 'llm_decision':
        input_text = payload.get('input', '')
        input_preview = input_text if len(input_text) <= 50 else input_text[:50] + "..."
        return f"🧠 **Decision:** {payload.get('decision', 'N/A')} (Input: \"{input_preview}\")"
    elif event_type == 'tool_call':
        return f"🔧 **Calling Tool:** {payload.get('tool', 'N/A')}"
    elif event_type == 'tool_result':
        success = "✅" if payload.get('success') else "❌"
        output = payload.get('output', '')
        output_preview = output if len(str(output)) <= 100 else str(output)[:100] + "..."
        return f"{success} **Tool Result:** Success={payload.get('success', False)}"
    elif event_type == 'hitl_request':
        return f"🤝 **Human Input Required:** {payload.get('reason', 'N/A')}"
    else:
        return f"ℹ️ {event_type}"

def group_events_into_steps(events):
    """Group events into logical steps based on patterns"""
    steps = []
    current_step = None
    
    for event in events:
        event_type = event.get('type', '')
        formatted = format_event(event)
        
        # Start new step for major actions
        if event_type == 'llm_decision':
            if current_step:
                steps.append(current_step)
            decision = event['payload'].get('decision', 'unknown')
            if decision == 'math':
                current_step = {'label': 'Intent Analysis → Math', 'icon': '💭', 'events': [formatted]}
            elif decision == 'theory':
                current_step = {'label': 'Intent Analysis → Search', 'icon': '💭', 'events': [formatted]}
            elif decision == 'ambiguous':
                current_step = {'label': 'Intent Analysis → Human Input Needed', 'icon': '💭', 'events': [formatted]}
            else:
                current_step = {'label': 'Intent Analysis', 'icon': '💭', 'events': [formatted]}
        
        elif event_type == 'tool_call':
            if current_step:
                steps.append(current_step)
            tool_name = event['payload'].get('tool', 'unknown')
            current_step = {'label': f'Executing {tool_name}', 'icon': '🔧', 'events': [formatted]}
        
        elif event_type == 'hitl_request':
            if current_step:
                steps.append(current_step)
            current_step = {'label': 'Human Input Required', 'icon': '🤝', 'events': [formatted]}
        
        else:
            # Add to current step or create generic step
            if current_step:
                current_step['events'].append(formatted)
            else:
                current_step = {'label': 'Processing', 'icon': '⚙️', 'events': [formatted]}
    
    # Add final step
    if current_step:
        steps.append(current_step)
    
    return steps

def chat_with_agent(message, history):
    """
    Streaming interface function for Gradio ChatInterface.
    Polls logger events in real-time to show streaming output.
    """
    
    # Clear previous events from logger
    logger.events.clear()
    
    # Initialize response
    yield "🤖 **Agent Processing...**\n\n*Initializing...*"
    
    try:
        # Run graph in background thread
        result_container = {}
        def run_graph():
            result_container['output'] = graph.invoke({"user_input": message})
        
        graph_thread = threading.Thread(target=run_graph)
        graph_thread.start()
        
        # Poll logger events while graph is running
        displayed_event_count = 0
        
        while graph_thread.is_alive() or displayed_event_count < len(logger.events):
            # Get new events
            current_event_count = len(logger.events)
            
            if current_event_count > displayed_event_count:
                # New events available
                all_events = logger.events[:current_event_count]
                steps = group_events_into_steps(all_events)
                
                # Build response with accordions
                response = "🤖 **Agent Processing...**\n\n"
                
                for i, step in enumerate(steps, 1):
                    events_text = "\n\n".join(step['events'])
                    
                    # Create accordion (open for the last step, closed for others)
                    is_open = "open" if i == len(steps) else ""
                    
                    accordion = f"""<details {is_open}>
<summary>{step['icon']} <b>Step {i}: {step['label']}</b></summary>

<div style="padding: 10px; margin: 5px 0;">

{events_text}

</div>

</details>

"""
                    response += accordion
                
                yield response
                displayed_event_count = current_event_count
            
            # Small delay before next poll
            time.sleep(0.1)
        
        # Wait for graph to complete
        graph_thread.join()
        
        # Get final answer
        graph_output = result_container['output'].get('graph_output', '')
        
        if "Answer:" in graph_output:
            parts = graph_output.split("-- Debug trace --")
            final_answer = parts[0].replace("Answer:", "").strip()
        else:
            final_answer = graph_output
        
        # Build final response with all steps collapsed
        all_events = logger.events
        steps = group_events_into_steps(all_events)
        
        response = ""
        for i, step in enumerate(steps, 1):
            events_text = "\n\n".join(step['events'])
            
            accordion = f"""<details>
<summary>{step['icon']} <b>Step {i}: {step['label']}</b></summary>

<div style="padding: 10px; margin: 5px 0;">

{events_text}

</div>

</details>

"""
            response += accordion
        
        # Add final answer
        response += f"\n\n---\n\n### 🎯 **Final Answer:**\n\n{final_answer}"
        yield response
        
    except Exception as e:
        import traceback
        yield f"❌ **Error:** {str(e)}\n\n```\n{traceback.format_exc()}\n```"

with gr.Blocks(title="InsightGraph") as demo:
    # ---- HEADER ----
    gr.Markdown(
        """
        # InsightGraph <sub><small>v4: 01 Jan 2025</small></sub>
        """,
        elem_id="header"
    )

    # ---- TABS ----
    with gr.Tabs():
        with gr.Tab("Chat"):
            gr.ChatInterface(
                chat_with_agent,
            )

        with gr.Tab("Graph"):
            gr.Markdown("### Graph View Placeholder\nUpload or render graph here.")

        with gr.Tab("Editor"):
            gr.Textbox(
                label="Editor",
                placeholder="Write or edit your text here...",
                lines=12
            )

        with gr.Tab("Settings"):
            gr.Checkbox(label="Enable debug mode")
            gr.Dropdown(["Light", "Dark"], label="Theme")
            gr.Textbox(label="API Key (optional)", type="password")

demo.launch()