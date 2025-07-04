import streamlit as st
import requests
import uuid

# Configure page
st.set_page_config(
    page_title="KAUTIOS : Calendar Managing Assistant", 
    page_icon="📅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme styling
st.markdown("""
<style>
    body, .main-header, .chat-message, .user-message, .assistant-message, .booking-success, .status-indicator, .instruction-box, .warning-box {
        font-family: 'Arial', sans-serif;
        color: white !important;
    }
    .main-header {
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 0.5em;
        color: white !important;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        background-color: #121212 !important;
    }
    .user-message {
        background-color: #1e1e1e !important;
        margin-left: 2rem;
        color: white !important;
    }
    .assistant-message {
        background-color: #2c2c2c !important;
        margin-right: 2rem;
        color: white !important;
    }
    .booking-success {
        background-color: #004d00 !important;
        border: 2px solid #4caf50;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #4caf50 !important;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    .status-online {
        background-color: #4caf50;
    }
    .status-offline {
        background-color: #f44336;
    }
    .instruction-box {
        background-color: #1e1e1e !important;
        border: 2px solid #444444;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white !important;
    }
    .warning-box {
        background-color: #3a3a3a !important;
        border: 2px solid #666666;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #ffcc00 !important;
    }
    body {
        background-color: #121212 !important;
    }
    .stTextInput > div > div > input {
        background-color: #1e1e1e !important;
        color: white !important;
        border: 1px solid #444444 !important;
    }
    .stSelectbox > div > div > div {
        background-color: #1e1e1e !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "backend_url" not in st.session_state:
    st.session_state.backend_url = 'https://kautios.onrender.com'
if "user_calendar_id" not in st.session_state:
    st.session_state.user_calendar_id = "primary"

# Sidebar
with st.sidebar:
    st.title("🔧 Settings")
    
    # st.subheader("🔗 Backend Configuration")
    # backend_url = st.text_input("Backend URL", value=st.session_state.backend_url, help="Enter your backend URL")
    # if backend_url != st.session_state.backend_url:
    #     st.session_state.backend_url = backend_url
    
    st.subheader("📅 Calendar Settings")
    user_calendar_id = st.text_input("Your Calendar ID", value=st.session_state.user_calendar_id, help="Enter your Google Calendar ID")
    if user_calendar_id != st.session_state.user_calendar_id:
        st.session_state.user_calendar_id = user_calendar_id
    
    if st.button("🔍 How to find my Calendar ID"):
        st.info("To find your Calendar ID, go to Google Calendar, select your calendar, click 'Settings and sharing', and copy the Calendar ID.")
    
    st.subheader("🔍 Connection Status")
    try:
        response = requests.get(f"{st.session_state.backend_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            calendar_status = health_data.get("calendar_service", False)
            st.markdown(f'<span class="status-indicator status-online"></span> **Backend: Online**', unsafe_allow_html=True)
            # st.success(f"✅ Connected to: {st.session_state.backend_url}")
            if calendar_status:
                st.markdown(f'<span class="status-indicator status-online"></span> **Calendar: Connected**', unsafe_allow_html=True)
                # st.success("✅ Google Calendar service is working!")
            else:
                st.markdown(f'<span class="status-indicator status-offline"></span> **Calendar: Disconnected**', unsafe_allow_html=True)
                st.error("❌ Google Calendar not configured. Please check service account credentials.")
        else:
            st.markdown(f'<span class="status-indicator status-offline"></span> **Backend: Offline**', unsafe_allow_html=True)
            st.error(f"❌ Backend returned status code: {response.status_code}")
    except Exception as e:
        st.markdown(f'<span class="status-indicator status-offline"></span> **Backend: Connection Error**', unsafe_allow_html=True)
        st.error(f"❌ Connection error: {str(e)}")
        st.info("💡 Make sure your backend is running and the URL is correct.")
    
    if st.button("🔍 Test Calendar Access"):
        try:
            validate_response = requests.post(f"{st.session_state.backend_url}/validate-calendar", json={"calendar_id": st.session_state.user_calendar_id}, timeout=10)
            if validate_response.status_code == 200:
                data = validate_response.json()
                if data.get("valid"):
                    st.success(f"✅ {data.get('message')}")
                else:
                    st.error(f"❌ {data.get('message')}")
            else:
                st.error("Failed to validate calendar access")
        except Exception as e:
            st.error(f"Validation request failed: {str(e)}")
    
    st.divider()
    
    st.subheader("📊 Session Info")
    st.text(f"Session ID: {st.session_state.session_id[:8]}...")
    st.text(f"Messages: {len(st.session_state.messages)}")
    st.text(f"Calendar ID: {st.session_state.user_calendar_id}")
    
    if st.button("🗑️ Clear Conversation", type="secondary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    st.divider()
    
    st.subheader("💡 How to Use")
    st.markdown("""
    1. Grant calendar access
    2. Enter your Calendar ID
    3. Start a conversation
    4. Request an appointment
    5. Provide details
    6. Confirm booking
    """)

# Main interface
st.markdown('<h1 class="main-header">📅 Calendar Booking Assistant</h1>', unsafe_allow_html=True)

# Setup Instructions
st.markdown("## 🚀 First Time Setup Instructions")

if "@group.calendar.google.com" in st.session_state.user_calendar_id:
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ Group Calendar Detected</h4>
        <p>Make sure you have admin access and the service account has access.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="instruction-box">
    <h3>📋 Grant Calendar Access to the Service Account</h3>
    <p>Grant access to the service account email with 'Make changes to events' permission.</p>
    <div style="background-color: #2c2c2c; border: 1px solid #555555; padding: 1rem; margin: 1rem 0; border-radius: 0.25rem; font-family: monospace; word-break: break-all; color: #00ff00;">
        mohit-chat-model@careful-century-464605-b4.iam.gserviceaccount.com
    </div>
    <p>Test connection using the sidebar button and start chatting!</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
**Welcome to your AI-powered calendar booking assistant! I can help you:**
- Check calendar availability
- Suggest available time slots
- Book appointments
- Schedule recurring meetings
""")

st.subheader("💬 Chat")

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
                if message.get("booking_made", False):
                    st.markdown("""
                    <div class="booking-success">
                        <h4>🎉 Booking Confirmed!</h4>
                        <p>Your appointment has been successfully added to your calendar.</p>
                    </div>
                    """, unsafe_allow_html=True)

def send_message(message=None):
    user_message = message if message is not None else st.session_state.get("user_input", "")
    if user_message:
        st.session_state.messages.append({"role": "user", "content": user_message})
        try:
            with st.spinner("🤔 Thinking..."):
                response = requests.post(f"{st.session_state.backend_url}/chat", json={"message": user_message, "session_id": st.session_state.session_id, "calendar_id": st.session_state.user_calendar_id}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                assistant_message = {"role": "assistant", "content": data["response"], "booking_made": data.get("booking_made", False), "booking_details": data.get("booking_details")}
                st.session_state.messages.append(assistant_message)
                if data.get("booking_made", False):
                    st.success("🎉 Appointment booked successfully!")
                    st.balloons()
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            st.info("💡 Check if your backend URL is correct and the server is running.")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
        if message is None:
            st.session_state.user_input = ""

st.text_input("Type your message here...", key="user_input", placeholder="e.g., 'I need to book a meeting for tomorrow at 2 PM'", on_change=send_message, label_visibility="collapsed")

st.subheader("💭 Example Prompts")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("📅 Book a meeting", key="example1", on_click=send_message, args=("I need to book a meeting for tomorrow",))
with col2:
    st.button("🔍 Check availability", key="example2", on_click=send_message, args=("What's my availability for this week?",))
with col3:
    st.button("⏰ Schedule appointment", key="example3", on_click=send_message, args=("Schedule a 1-hour appointment",))

with st.expander("🔧 Troubleshooting"):
    st.markdown("""
    **Common Issues:**
    1. Calendar Disconnected
    2. Backend Connection Error
    3. Group Calendar Issues
    4. Permission Errors
    """)

st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9em;">
    <p>Powered by FastAPI, LangGraph, and Google Calendar API</p>
    <p>Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
