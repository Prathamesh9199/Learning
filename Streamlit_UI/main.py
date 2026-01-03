import streamlit as st
import time

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(
    layout="wide",
    page_title="Osaka Trip Planner",
    page_icon="🌸",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "content": "Plan a trip to Osaka for Sakura season next spring!"},
        {
            "role": "assistant",
            "content": "That sounds magical! 🌸 Osaka is beautiful in early April. I've initialized the **Planner** with a map of Osaka Castle Park. \n\nShall we look at the cherry blossom forecast or start booking food spots?",
            "show_cards": True
        }
    ]
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Planner"

# --- 3. CSS STYLING (The "Anthropic" Theme) ---
st.markdown("""
<style>
    /* GLOBAL FONTS & THEME */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #414141;
    }

    /* REMOVE DEFAULT HEADER & PADDING */
    header[data-testid="stHeader"] { display: none; }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* CUSTOM COMPONENT STYLING */
    
    /* The Content Card (Right Side) */
    .content-card {
        background-color: white;
        border: 1px solid #E6E6E6;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: transparent;
    }
    .stChatMessage.user {
        background-color: #F7F7F8;
    }
    
    /* Button Styling Override */
    div.stButton > button {
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        background-color: white;
        color: #333;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #FFB7B2; /* Sakura Pink */
        color: #D65A68;
        background-color: #FFF5F5;
    }
    
    /* Active Tab Styling Hack for Buttons */
    button[data-testid="baseButton-primary"] {
        background-color: #FFF0F0 !important;
        border-color: #FFB7B2 !important;
        color: #D65A68 !important;
        font-weight: 600;
    }

    /* Sidebar Minimalist */
    section[data-testid="stSidebar"] {
        width: 70px !important;
        background-color: #FAFAFA;
        border-right: 1px solid #EFEFEF;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent; 
    }
    ::-webkit-scrollbar-thumb {
        background: #E0E0E0; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #C0C0C0; 
    }

</style>
""", unsafe_allow_html=True)


# --- 4. SIDEBAR NAVIGATION (Icon Rail) ---
with st.sidebar:
    st.markdown("### 🌸", unsafe_allow_html=True) # Logo placeholder
    st.write("") # Spacer
    
    if st.button("➕", help="New Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # We use a trick here: these buttons update a state but don't navigate pages
    if st.button("🗺️", help="Planner View"):
        st.session_state.active_tab = "Planner"
        st.rerun()
        
    if st.button("📅", help="Forecast"):
        st.session_state.active_tab = "Forecast"
        st.rerun()
        
    if st.button("🍜", help="Food Guide"):
        st.session_state.active_tab = "Food"
        st.rerun()

    # Bottom Profile
    st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True) 
    st.caption("v2.1")


# --- 5. MAIN INTERFACE ---

# Layout: 40% Chat | 60% Workspace
col_chat, col_workspace = st.columns([2, 3], gap="large")

# === LEFT COLUMN: CHAT ===
with col_chat:
    st.markdown("#### 💬 Chat")
    
    # Use native container with fixed height for independent scrolling
    chat_container = st.container(height=650)
    
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🌸" if msg["role"] == "assistant" else "👤"):
                st.write(msg["content"])
                
                # Contextual buttons inside chat
                if msg.get("show_cards"):
                    st.caption("Suggested Actions:")
                    c1, c2 = st.columns(2)
                    if c1.button("View Map", key=f"btn_map_{msg['content'][:5]}"):
                        st.session_state.active_tab = "Planner"
                        st.rerun()
                    if c2.button("Check Dates", key=f"btn_date_{msg['content'][:5]}"):
                        st.session_state.active_tab = "Forecast"
                        st.rerun()

    # Chat Input (Pinned to bottom of column conceptually, but natively sits at bottom of screen)
    # To make it feel like it belongs to the left column, we rely on the layout.
    if prompt := st.chat_input("Ask about Osaka..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Simulate simple "AI" logic
        response_content = f"I've noted your request about: **{prompt}**. I'm updating the workspace with relevant info."
        
        # Simple routing logic
        if "food" in prompt.lower() or "sushi" in prompt.lower():
            st.session_state.active_tab = "Food"
            response_content = "I've switched the workspace to the **Food Guide**. Here are some top rated sushi spots in Dotonbori."
        elif "date" in prompt.lower() or "when" in prompt.lower():
            st.session_state.active_tab = "Forecast"
            response_content = "Checking the latest cherry blossom forecast for 2026..."
            
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun()


# === RIGHT COLUMN: WORKSPACE ===
with col_workspace:
    # Top Navigation Bar for Workspace
    st.markdown(f"#### 📂 Workspace: {st.session_state.active_tab}")
    
    # Tab Navigation (Visual)
    t_cols = st.columns([1,1,1,3])
    def tab_btn(label, tab_name):
        is_active = st.session_state.active_tab == tab_name
        if t_cols[0 if tab_name=="Planner" else 1 if tab_name=="Forecast" else 2].button(
            label, 
            key=f"tab_{tab_name}", 
            use_container_width=True, 
            type="primary" if is_active else "secondary"
        ):
            st.session_state.active_tab = tab_name
            st.rerun()

    tab_btn("Planner", "Planner")
    tab_btn("Forecast", "Forecast")
    tab_btn("Food", "Food")

    # Scrollable Content Area
    workspace_container = st.container(height=600)
    
    with workspace_container:
        # Dynamic Content
        if st.session_state.active_tab == "Planner":
            st.info("📍 Currently viewing: **Osaka Castle Park**")
            
            # Map Placeholder (Using HTML/CSS for a nice card look)
            st.markdown("""
            <div class="content-card" style="text-align: center; height: 300px; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #f9f9f9; border: 2px dashed #ccc;">
                <div style="font-size: 64px;">🏯</div>
                <h3 style="margin-top: 10px;">Interactive Map</h3>
                <p style="color: #666;">Mapbox / Google Maps Integration would go here</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 📝 Itinerary Draft")
            st.markdown("""
            - **09:00 AM** - Arrival at Osaka Castle (Otemon Gate)
            - **10:30 AM** - Nishinomaru Garden (Best Sakura Spot)
            - **12:00 PM** - Lunch at Jo-Terrace Osaka
            """)

        elif st.session_state.active_tab == "Forecast":
            st.success("🌸 2026 Prediction: **Early Bloom Expected**")
            
            col_metrics1, col_metrics2 = st.columns(2)
            col_metrics1.metric("First Bloom", "March 24", "-2 days")
            col_metrics2.metric("Full Bloom", "April 02", "-1 day")
            
            st.markdown("### 📊 Bloom Probability")
            chart_data = {"Date": ["Mar 20", "Mar 25", "Mar 30", "Apr 05", "Apr 10"], "Bloom %": [10, 45, 80, 100, 60]}
            st.line_chart(chart_data, x="Date", y="Bloom %", color="#FFB7B2")
            
            st.markdown("""
            <div class="content-card">
                <b>Crowd Advisory:</b>
                <p>Weekends in early April will be "Red Alert" levels. Aim for Tuesday/Wednesday morning visits.</p>
            </div>
            """, unsafe_allow_html=True)

        elif st.session_state.active_tab == "Food":
            st.warning("⚠️ Reservations recommended 2 months in advance")
            
            st.markdown("### 🍜 Dotonbori Essentials")
            
            food_items = [
                {"name": "Takoyaki Wanaka", "type": "Street Food", "rating": "4.8⭐"},
                {"name": "Okonomiyaki Mizuno", "type": "Teppanyaki", "rating": "4.6⭐"},
                {"name": "Kushikatsu Daruma", "type": "Fried Skewers", "rating": "4.5⭐"},
            ]
            
            for item in food_items:
                st.markdown(f"""
                <div class="content-card" style="padding: 15px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{item['name']}</b>
                        <span style="background-color: #FFF5F5; color: #D65A68; padding: 2px 8px; border-radius: 4px;">{item['rating']}</span>
                    </div>
                    <div style="color: #666; font-size: 0.9em;">{item['type']}</div>
                </div>
                """, unsafe_allow_html=True)