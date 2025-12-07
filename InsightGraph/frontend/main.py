import gradio as gr
import sys
from pathlib import Path
import time
import threading

# Add parent directory to path to import agent module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Note: This assumes the agent module exists in your environment
try:
    from agent.main import graph, logger
except ImportError:
    # Fallback for the purpose of the UI demo if agent is missing
    class MockLogger:
        def __init__(self): self.events = []
    logger = MockLogger()
    graph = None

# --- FORMATTING LOGIC ---
def format_event(event):
    """Format a logger event into readable text using minimal HTML/Markdown"""
    event_type = event.get('type', 'unknown')
    payload = event.get('payload', {})

    if event_type == 'thought':
        return f"<div>💭 {payload.get('thought', '')}</div>"
    elif event_type == 'llm_decision':
        decision = payload.get('decision', 'N/A')
        return f"<div>🧠 <b>Decision:</b> <code>{decision}</code></div>"
    elif event_type == 'tool_call':
        tool = payload.get('tool', 'N/A')
        return f"<div>🔧 <b>Tool:</b> <code>{tool}</code></div>"
    elif event_type == 'tool_result':
        success = payload.get('success', False)
        icon = "✅" if success else "❌"
        return f"<div>{icon} <b>Result:</b> {'Success' if success else 'Failed'}</div>"
    elif event_type == 'hitl_request':
        return f"<div>🤝 <b>Human Input Required:</b> {payload.get('reason', 'N/A')}</div>"
    else:
        return f"<div>ℹ️ {event_type}</div>"

def group_events_into_steps(events):
    """Group events into logical steps based on patterns"""
    steps = []
    current_step = None
    
    for event in events:
        event_type = event.get('type', '')
        formatted = format_event(event)
        
        if event_type == 'llm_decision':
            if current_step: steps.append(current_step)
            decision = event['payload'].get('decision', 'unknown')
            label = f"Intent Analysis → {decision.capitalize()}"
            current_step = {'label': label, 'icon': '💭', 'events': [formatted]}
        elif event_type == 'tool_call':
            if current_step: steps.append(current_step)
            tool_name = event['payload'].get('tool', 'unknown')
            current_step = {'label': f'Executing {tool_name}', 'icon': '🔧', 'events': [formatted]}
        elif event_type == 'hitl_request':
            if current_step: steps.append(current_step)
            current_step = {'label': 'Human Input Required', 'icon': '🤝', 'events': [formatted]}
        else:
            if current_step:
                current_step['events'].append(formatted)
            else:
                current_step = {'label': 'Processing', 'icon': '⚙️', 'events': [formatted]}
    
    if current_step:
        steps.append(current_step)
    return steps

# --- CORE AGENT LOGIC ---
def chat_with_agent(message, history):
    """
    Original streaming logic.
    """
    if not hasattr(logger, 'events'):
        yield "⚠️ **Error:** Agent logger not found."
        return

    logger.events.clear()
    yield "🤖 **Agent Processing...**"
    
    try:
        # Run graph in background thread
        result_container = {}
        def run_graph():
            if graph:
                result_container['output'] = graph.invoke({"user_input": message})
            else:
                time.sleep(2) 
                result_container['output'] = {"graph_output": "Agent mocked response."}

        graph_thread = threading.Thread(target=run_graph)
        graph_thread.start()
        
        displayed_event_count = 0
        
        while graph_thread.is_alive() or displayed_event_count < len(logger.events):
            current_event_count = len(logger.events)
            if current_event_count > displayed_event_count:
                all_events = logger.events[:current_event_count]
                steps = group_events_into_steps(all_events)
                
                response = "### 🤖 Agent Processing\n\n"
                for i, step in enumerate(steps, 1):
                    events_text = "\n".join(step['events'])
                    is_open = "open" if i == len(steps) else ""
                    accordion = f"""
<details {is_open}>
<summary>{step['icon']} Step {i}: {step['label']}</summary>
<div style="padding-left: 1em; margin-top: 0.5em;">
{events_text}
</div>
</details>
"""
                    response += accordion
                yield response
                displayed_event_count = current_event_count
            time.sleep(0.1)
        
        graph_thread.join()
        
        # Get final answer
        graph_output = result_container['output'].get('graph_output', '')
        if "Answer:" in graph_output:
            final_answer = graph_output.split("Answer:")[1].split("-- Debug trace --")[0].strip()
        else:
            final_answer = graph_output
        
        # Re-render full history collapsed
        all_events = logger.events
        steps = group_events_into_steps(all_events)
        response = ""
        for i, step in enumerate(steps, 1):
            events_text = "\n".join(step['events'])
            accordion = f"""
<details>
<summary>{step['icon']} Step {i}: {step['label']}</summary>
<div style="padding-left: 1em; margin-top: 0.5em;">
{events_text}
</div>
</details>
"""
            response += accordion

        response += f"""
---
### 🎯 Final Answer
{final_answer}
"""
        yield response
        
    except Exception as e:
        yield f"❌ **Error:** {str(e)}"

# --- UI EVENT HANDLERS ---
def interact(message, history, model_mode):
    """
    Wrapper to handle the chat interaction manually.
    """
    if not message.strip():
        yield history, ""
        return

    # 1. Append User Message
    history = history + [{"role": "user", "content": message}]
    yield history, "" # Update UI immediately, clear input box

    # 2. Append Empty Bot Message (placeholder)
    history.append({"role": "assistant", "content": ""})
    
    # 3. Call the Agent Logic
    print(f"DEBUG: Using model mode: {model_mode}") 
    
    generator = chat_with_agent(message, history)
    
    for partial_response in generator:
        history[-1]["content"] = partial_response
        yield history, ""

# New: Suggestions Logic
def toggle_suggestions(text):
    """Show suggestions only if text contains '/'"""
    # Simple logic: if text ends with / or is just /, show it.
    if text.strip().endswith("/"):
        return gr.update(visible=True)
    return gr.update(visible=False)

def use_suggestion(selection):
    """When a suggestion is clicked, put it in the box and hide suggestions"""
    # selection is a list of the values in the row, e.g. ["23-9"]
    if not selection:
        return "", gr.update(visible=False)
    return selection[0], gr.update(visible=False)

# --- UI DEFINITION ---
with gr.Blocks(title="InsightGraph") as demo:
    
    gr.Markdown("# InsightGraph v4 <sub><small>v4: 8th December 2025</sub></small>")

    with gr.Tabs():
        with gr.Tab("💬 Chat"):
            
            # 1. Chatbot Display
            chatbot = gr.Chatbot(
                height=500, 
                show_label=False,
            )
            
            # 2. Suggestions (Hidden by default)
            sample_questions = [
                ["Who was the chancellor of Germany in 1912?"],
                ["23-9"],
                ["lkaj234kl"]
            ]
            
            suggestions_box = gr.Dataset(
                label="Sample Questions",
                components=[gr.Textbox(visible=False)], 
                samples=sample_questions,
                visible=False, # Initially hidden
            )

            # 3. The "Gemini-Style" Integrated Input Bar
            with gr.Group():
                with gr.Row(variant="panel", equal_height=True):
                    
                    # A. Main Text Input
                    msg = gr.Textbox(
                        placeholder="Ask me anything... (Type '/' for samples)",
                        container=False,
                        scale=8,
                        autofocus=True,
                        show_label=False,
                        lines=1
                    )
                    
                    # B. Model Settings Dropdown (Integrated)
                    model_selector = gr.Dropdown(
                        choices=["Fast", "Think", "Deep Think"],
                        value="Fast",
                        container=False,
                        scale=2,
                        show_label=False,
                        interactive=True,
                        min_width=100
                    )
                    
                    # C. Submit Button
                    submit_btn = gr.Button(
                        "➤", 
                        variant="primary",
                        scale=1,
                        min_width=50,
                        size="sm"
                    )

            # --- Event Wiring ---

            # A. Slash Command Logic
            msg.change(
                fn=toggle_suggestions,
                inputs=msg,
                outputs=suggestions_box
            )

            # --- FIX APPLIED HERE: Added inputs=suggestions_box ---
            suggestions_box.click(
                fn=use_suggestion,
                inputs=suggestions_box, 
                outputs=[msg, suggestions_box]
            )

            # B. Chat Submission Logic
            submit_btn.click(
                fn=interact,
                inputs=[msg, chatbot, model_selector],
                outputs=[chatbot, msg]
            ).then(
                fn=lambda: gr.update(visible=False),
                outputs=suggestions_box
            )
            
            msg.submit(
                fn=interact,
                inputs=[msg, chatbot, model_selector],
                outputs=[chatbot, msg]
            ).then(
                fn=lambda: gr.update(visible=False),
                outputs=suggestions_box
            )

        with gr.Tab("📊 Graph"):
            gr.Markdown("### Graph Visualization")
            gr.Markdown("_Upload or render your graph here._")

        with gr.Tab("✏️ Editor"):
            gr.Textbox(
                label="Text Editor",
                placeholder="Write or edit your text here...",
                lines=15
            )

        with gr.Tab("⚙️ Settings"):
            gr.Markdown("### Preferences")
            gr.Checkbox(label="Enable debug mode", value=False)
            gr.Dropdown(["Light", "Dark", "Auto"], label="Theme", value="Light")
            gr.Markdown("### API Configuration")
            gr.Textbox(label="API Key", type="password")

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Base())