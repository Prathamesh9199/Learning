import gradio as gr
import sys
from pathlib import Path
import time
import threading

# Add parent directory to path to import agent module
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import graph, logger

def format_event(event):
    """Format a logger event into readable text with modern styling"""
    event_type = event.get('type', 'unknown')
    payload = event.get('payload', {})

    if event_type == 'thought':
        return f"<div style='padding: 0.5rem 0; color: #4b5563;'>💭 {payload.get('thought', '')}</div>"
    elif event_type == 'llm_decision':
        input_text = payload.get('input', '')
        input_preview = input_text if len(input_text) <= 50 else input_text[:50] + "..."
        decision = payload.get('decision', 'N/A')
        return f"<div style='padding: 0.5rem 0;'><span style='color: #667eea; font-weight: 600;'>🧠 Decision:</span> <code style='background: #f3f4f6; padding: 0.2rem 0.5rem; border-radius: 4px;'>{decision}</code></div>"
    elif event_type == 'tool_call':
        tool = payload.get('tool', 'N/A')
        return f"<div style='padding: 0.5rem 0;'><span style='color: #667eea; font-weight: 600;'>🔧 Tool:</span> <code style='background: #f3f4f6; padding: 0.2rem 0.5rem; border-radius: 4px;'>{tool}</code></div>"
    elif event_type == 'tool_result':
        success = payload.get('success', False)
        icon = "✅" if success else "❌"
        color = "#10b981" if success else "#ef4444"
        return f"<div style='padding: 0.5rem 0; color: {color};'>{icon} <span style='font-weight: 600;'>Result:</span> {'Success' if success else 'Failed'}</div>"
    elif event_type == 'hitl_request':
        return f"<div style='padding: 0.5rem 0; color: #f59e0b;'><span style='font-weight: 600;'>🤝 Human Input Required:</span> {payload.get('reason', 'N/A')}</div>"
    else:
        return f"<div style='padding: 0.5rem 0; color: #6b7280;'>ℹ️ {event_type}</div>"

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
                response = "<div style='text-align: center; padding: 1rem; color: #667eea; font-size: 1.1rem; font-weight: 600;'>🤖 Agent Processing...</div>\n\n"

                for i, step in enumerate(steps, 1):
                    events_text = "\n".join(step['events'])

                    # Create accordion (open for the last step, closed for others)
                    is_open = "open" if i == len(steps) else ""

                    accordion = f"""<details {is_open}>
<summary><span style='font-size: 0.9rem;'>{step['icon']} Step {i}:</span> {step['label']}</summary>

<div style="padding: 0.75rem; margin: 0.5rem 0;">
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
            events_text = "\n".join(step['events'])

            accordion = f"""<details>
<summary><span style='font-size: 0.9rem;'>{step['icon']} Step {i}:</span> {step['label']}</summary>

<div style="padding: 0.75rem; margin: 0.5rem 0;">
{events_text}
</div>

</details>

"""
            response += accordion

        # Add final answer with modern styling
        response += f"""

<div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-left: 4px solid #667eea; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem;">
<div style="font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 0.75rem;">🎯 Final Answer</div>
<div style="color: #1f2937; line-height: 1.6;">

{final_answer}

</div>
</div>
"""
        yield response
        
    except Exception as e:
        import traceback
        yield f"❌ **Error:** {str(e)}\n\n```\n{traceback.format_exc()}\n```"

# Custom CSS for modern, minimalistic light theme
custom_css = """
/* Global Styles */
#root, body, html {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

.gradio-container {
    width: 100% !important;
    max-width: 3000px !important;   /* You can change this */
    margin: 0 auto !important;
    padding: 0 2rem !important;
}

/* Makes Blocks stretch full width */
.gr-block {
    width: 100% !important;
    max-width: 100% !important;
}

/* Make ChatInterface container full width */
.gradio-chatbot {
    width: 100% !important;
    max-width: 100% !important;
}


/* Header Styling */
#header {
    text-align: left;
    padding: 0;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

#header h1 {
    font-size: 2.25rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.02em;
}

#header p {
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

/* Tab Styling */
.tab-nav {
    border-bottom: 2px solid #f3f4f6;
    padding: 0 1rem;
}

button.selected {
    color: #667eea !important;
    border-bottom-color: #667eea !important;
}

/* Chat Container */
.chatbot {
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    background: #ffffff !important;
    font-size: 1rem !important;
}

/* Main content area */
.contain {
    max-width: 100% !important;
}

/* Tab content */
.tabitem {
    padding: 1.5rem !important;
}

/* Message Bubbles */
.message {
    border-radius: 8px !important;
}

.message.user {
    background: #f3f4f6 !important;
}

.message.bot {
    background: #ffffff !important;
}

/* Accordions / Details */
details {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 0.75rem;
    margin: 0.5rem 0;
    transition: all 0.2s ease;
}

details:hover {
    border-color: #d1d5db;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

details[open] {
    background: #ffffff;
}

details summary {
    cursor: pointer;
    font-weight: 600;
    color: #374151;
    padding: 0.25rem;
    user-select: none;
    list-style: none;
}

details summary::-webkit-details-marker {
    display: none;
}

details summary::before {
    content: '▶';
    display: inline-block;
    margin-right: 0.5rem;
    transition: transform 0.2s;
    color: #667eea;
}

details[open] summary::before {
    transform: rotate(90deg);
}

/* Input Fields */
textarea, input {
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 1rem 1.25rem !important;
    font-size: 1rem !important;
    transition: border-color 0.2s ease !important;
}

textarea:focus, input:focus {
    border-color: #667eea !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Buttons */
button {
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    border: 1px solid #e5e7eb !important;
}

button.primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
}

button.primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
}

button:hover {
    background: #f9fafb !important;
    border-color: #d1d5db !important;
}

/* Loading State */
.loading {
    display: inline-block;
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Final Answer Styling */
.final-answer {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-left: 4px solid #667eea;
    padding: 1.5rem;
    border-radius: 8px;
    margin-top: 1rem;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f3f4f6;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
}
"""

with gr.Blocks(title="InsightGraph") as demo:
    # Inject custom CSS
    gr.HTML(f"<style>{custom_css}</style>")
    # ---- HEADER ----
    gr.Markdown(
        """
        # InsightGraph <span style="color: #6b7280; font-size: 0.9rem; margin-top: 0.5rem;">v4: 8th December 2025</span>
        """,
        elem_id="header"
    )

    # ---- TABS ----
    with gr.Tabs():
        with gr.Tab("💬 Chat"):
            gr.ChatInterface(
                chat_with_agent,
                chatbot=gr.Chatbot(height=650, show_label=False),
                textbox=gr.Textbox(
                    placeholder="Ask me anything...",
                    show_label=False,
                    container=False
                )
            )

        with gr.Tab("📊 Graph"):
            gr.Markdown(
                """
                ### Graph Visualization
                <p style="color: #6b7280;">Upload or render your graph here.</p>
                """,
                elem_classes="tab-content"
            )

        with gr.Tab("✏️ Editor"):
            gr.Textbox(
                label="Text Editor",
                placeholder="Write or edit your text here...",
                lines=15,
                show_label=True
            )

        with gr.Tab("⚙️ Settings"):
            with gr.Group():
                gr.Markdown("### Preferences")
                gr.Checkbox(label="Enable debug mode", value=False)
                gr.Dropdown(["Light", "Dark", "Auto"], label="Theme", value="Light")

            with gr.Group():
                gr.Markdown("### API Configuration")
                gr.Textbox(label="API Key (optional)", type="password", placeholder="Enter your API key")

demo.launch()