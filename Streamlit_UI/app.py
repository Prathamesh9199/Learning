import gradio as gr
import time

# --- 1. THEME & CSS ---
# We create a clean, soft theme and inject custom CSS for the specific "Card" look
theme = gr.themes.Soft(
    primary_hue="rose",
    neutral_hue="slate",
    spacing_size="sm",
    radius_size="md",
    font=["Inter", "ui-sans-serif", "system-ui"]
).set(
    body_background_fill="#F9FAFB",
    block_background_fill="#FFFFFF",
    block_border_width="1px",
    block_shadow="0 2px 8px rgba(0,0,0,0.04)"
)

css = """
/* HIDE DEFAULT GRADIO FOOTER */
footer {visibility: hidden !important;}

/* CUSTOM SCROLLBARS */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #D1D5DB; }

/* CHAT BUBBLES */
.message-row { gap: 12px; }
.avatar-container { border-radius: 50%; border: 2px solid #FFE4E6; }

/* CONTENT CARDS IN WORKSPACE */
.content-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

/* SIDEBAR ICONS */
.sidebar-btn {
    font-size: 24px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-align: center !important;
    padding: 10px !important;
    color: #6B7280 !important;
}
.sidebar-btn:hover {
    background-color: #F3F4F6 !important;
    border-radius: 12px !important;
    color: #E11D48 !important; /* Rose color */
}
"""

# --- 2. LOGIC & MOCK DATA ---

# Initial Chat History
initial_history = [
    ["", "🌸 **Osaka Trip Planner**\n\nI've initialized the **Planner** tab for you. Would you like to check the **Forecast** or look at **Food** options?"]
]

def user_message(message, history):
    return "", history + [[message, None]]

def bot_response(history):
    user_msg = history[-1][0]
    # Simple keyword routing logic to switch tabs
    response_text = ""
    target_tab = gr.Tabs(selected=None) # Default: don't switch

    if "food" in user_msg.lower() or "sushi" in user_msg.lower():
        response_text = "I've switched your workspace to the **Food Guide**. 🍜\n\nDotonbori is the place to be! I've listed some top-rated spots."
        target_tab = gr.Tabs(selected="tab_food")
        
    elif "date" in user_msg.lower() or "when" in user_msg.lower() or "forecast" in user_msg.lower():
        response_text = "Checking the cherry blossom forecast... 🌸\n\nIt looks like early April is the sweet spot. I've updated the **Forecast** tab."
        target_tab = gr.Tabs(selected="tab_forecast")
        
    else:
        response_text = f"I've noted that: **{user_msg}**. \n\nYou can see the details in the **Planner** tab."
        target_tab = gr.Tabs(selected="tab_planner")

    # Simulate typing
    history[-1][1] = ""
    for char in response_text:
        history[-1][1] += char
        time.sleep(0.005)
        yield history, target_tab

def clear_chat():
    return initial_history

# --- 3. UI LAYOUT ---

with gr.Blocks(theme=theme, css=css, title="Osaka Planner") as demo:
    
    # State to hold chat history
    chat_state = gr.State(initial_history)

    with gr.Row(equal_height=True):
        
        # === A. NARROW SIDEBAR ===
        with gr.Column(scale=1, min_width=80, elem_classes="sidebar"):
            gr.Markdown("### 🌸", elem_id="logo")
            btn_new = gr.Button("➕", elem_classes="sidebar-btn")
            gr.HTML("<div style='height: 20px;'></div>") # Spacer
            btn_nav_plan = gr.Button("🗺️", elem_classes="sidebar-btn")
            btn_nav_fore = gr.Button("📅", elem_classes="sidebar-btn")
            btn_nav_food = gr.Button("🍜", elem_classes="sidebar-btn")
            
        # === B. CHAT INTERFACE (Left Main) ===
        with gr.Column(scale=6):
            gr.Markdown("### 💬 Chat Assistant")
            
            chatbot = gr.Chatbot(
                value=initial_history,
                elem_id="chatbot",
                avatar_images=("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", "https://api.dicebear.com/7.x/bottts/svg?seed=Sakura"),
                height=600,
                show_label=False
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about Osaka, Sakura dates, or Sushi...",
                    show_label=False,
                    scale=8,
                    container=False
                )
                btn_send = gr.Button("➤", scale=1, variant="primary")

        # === C. WORKSPACE / TABS (Right Main) ===
        with gr.Column(scale=8):
            gr.Markdown("### 📂 Workspace")
            
            # We give the Tabs component an ID so we can update it programmatically
            with gr.Tabs(elem_id="workspace_tabs") as workspace_tabs:
                
                # --- TAB 1: PLANNER ---
                with gr.TabItem("Planner", id="tab_planner"):
                    gr.HTML("""
                    <div class="content-card" style="text-align:center; height:300px; display:flex; flex-direction:column; justify-content:center; align-items:center; background:#FAFAFA;">
                        <div style="font-size:60px;">🏯</div>
                        <h3 style="color:#374151;">Osaka Castle Park Map</h3>
                        <p style="color:#9CA3AF;">Interactive Layer Loaded</p>
                    </div>
                    """)
                    
                    with gr.Group():
                        gr.Markdown("#### 📝 Itinerary Draft")
                        gr.Dataframe(
                            headers=["Time", "Activity", "Notes"],
                            value=[
                                ["09:00", "Osaka Castle", "Enter via Otemon Gate"],
                                ["11:30", "Kema Sakuranomiya", "River cruise"],
                                ["13:00", "Dotonbori", "Lunch & Street Food"]
                            ],
                            interactive=False
                        )

                # --- TAB 2: FORECAST ---
                with gr.TabItem("Forecast", id="tab_forecast"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("""
                            <div class="content-card" style="border-left: 5px solid #F43F5E;">
                                <h3 style="margin:0; color:#F43F5E;">Expected Bloom</h3>
                                <p style="font-size:24px; font-weight:bold; margin:5px 0;">March 28 - April 05</p>
                                <small>Confidence: High (85%)</small>
                            </div>
                            """)
                        with gr.Column():
                             gr.HTML("""
                            <div class="content-card">
                                <h3 style="margin:0;">Crowd Level</h3>
                                <p style="font-size:24px; font-weight:bold; margin:5px 0;">Extreme 🔴</p>
                                <small>Avoid weekends if possible</small>
                            </div>
                            """)
                    
                    gr.LinePlot(
                        value=None, # Mock data handling would go here, using static image for demo reliability
                        x="Date", y="Bloom",
                        title="Bloom Probability Curve",
                        height=250,
                        show_label=False
                    )
                    gr.Markdown("*Interactive probability chart visualization placeholder*")

                # --- TAB 3: FOOD ---
                with gr.TabItem("Food Guide", id="tab_food"):
                    gr.HTML("""
                    <div class="content-card" style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h3 style="margin:0;">🍣 Endo Sushi</h3>
                            <p style="margin:0; color:gray;">Central Market • Omakase</p>
                        </div>
                        <div style="background:#FFE4E6; color:#BE123C; padding:5px 10px; border-radius:8px; font-weight:bold;">4.8 ⭐</div>
                    </div>
                    
                    <div class="content-card" style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h3 style="margin:0;">🐙 Wanaka Takoyaki</h3>
                            <p style="margin:0; color:gray;">Namba • Street Food</p>
                        </div>
                        <div style="background:#FFE4E6; color:#BE123C; padding:5px 10px; border-radius:8px; font-weight:bold;">4.6 ⭐</div>
                    </div>
                    """)
                    
                    btn_book = gr.Button("Find Reservations", variant="primary")
                    btn_book.click(lambda: "Redirecting to TableCheck...", None, None)

    # --- 4. EVENT WIRING ---

    # Chat Interaction
    # 1. User submits -> Update Chatbot (User msg)
    # 2. Bot processes -> Updates Chatbot (Stream) + Updates Active Tab
    # msg_input.submit(user_message, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
    #     bot_response, [chatbot], [chatbot, workspace_tabs]
    # )
    
    # btn_send.click(user_message, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
    #     bot_response, [chatbot], [chatbot, workspace_tabs]
    # )

    # Sidebar Navigation Wiring
    # These buttons explicitly force the tabs to switch
    btn_nav_plan.click(lambda: gr.Tabs(selected="tab_planner"), None, workspace_tabs)
    btn_nav_fore.click(lambda: gr.Tabs(selected="tab_forecast"), None, workspace_tabs)
    btn_nav_food.click(lambda: gr.Tabs(selected="tab_food"), None, workspace_tabs)
    
    # Reset
    btn_new.click(clear_chat, None, chatbot)

# --- 5. LAUNCH ---
if __name__ == "__main__":
    demo.launch()