import streamlit as st
import requests
import json
from datetime import datetime
import uuid

# Configure page 
st.set_page_config(
    page_title="KAUTIOS: Calendar Managing Assistant",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    .booking-success {
        background-color: #e8f5e8;
        border: 2px solid #4caf50;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #4caf50;
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
        background-color: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
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
    
    # Add calendar ID input
    st.subheader("📅 Calendar Settings")
    user_calendar_id = st.text_input(
        "Your Calendar ID", 
        value=st.session_state.user_calendar_id,
        help="Enter your Google Calendar ID. Use 'primary' for your main calendar, or paste a specific calendar ID."
    )
    
    # Store the calendar ID in session state
    if user_calendar_id != st.session_state.user_calendar_id:
        st.session_state.user_calendar_id = user_calendar_id
    
    # Update the chat request to include calendar ID
    if st.button("🔍 How to find my Calendar ID"):
        st.info("""
        To find your Calendar ID:
        1. Go to Google Calendar
        2. Click on your calendar name in the left sidebar
        3. Select 'Settings and sharing'
        4. Scroll to 'Integrate calendar' section
        5. Copy the Calendar ID (looks like an email)
        """)
    
    # Backend URL configuration
    backend_url = "http://localhost:8000"
    st.session_state.backend_url = backend_url
    
    # Test connection
    st.subheader("🔍 Connection Status")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            calendar_status = health_data.get("calendar_service", False)
            
            st.markdown(
                f'<span class="status-indicator status-online"></span> Backend: Online', 
                unsafe_allow_html=True
            )
            
            if calendar_status:
                st.markdown(
                    f'<span class="status-indicator status-online"></span> Calendar: Connected', 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<span class="status-indicator status-offline"></span> Calendar: Disconnected', 
                    unsafe_allow_html=True
                )
                st.warning("Google Calendar not configured. Please check service account credentials.")
        else:
            st.markdown(
                f'<span class="status-indicator status-offline"></span> Backend: Offline', 
                unsafe_allow_html=True
            )
    except Exception as e:
        st.markdown(
            f'<span class="status-indicator status-offline"></span> Backend: Connection Error', 
            unsafe_allow_html=True
        )
        st.error(f"Connection error: {str(e)}")
    
    st.divider()
    
    # Session info
    st.subheader("📊 Session Info")
    st.text(f"Session ID: {st.session_state.session_id[:8]}...")
    st.text(f"Messages: {len(st.session_state.messages)}")
    st.text(f"Calendar ID: {st.session_state.user_calendar_id}")
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation", type="secondary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    st.divider()
    
    # Instructions
    st.subheader("💡 How to Use")
    st.markdown("""
    1. **Grant calendar access** (see setup instructions below)
    2. **Enter your Calendar ID** above
    3. **Start a conversation** by typing a message
    4. **Request an appointment** by saying something like:
       - "I need to book a meeting"
       - "Schedule an appointment for tomorrow"
       - "Check availability for Friday at 2 PM"
    5. **Provide details** when asked:
       - Meeting title/subject
       - Preferred date
       - Preferred time
       - Duration
    6. **Confirm** the booking when prompted
    
    The assistant will check your calendar availability and book appointments automatically!
    """)

# Main interface
st.markdown('<h1 class="main-header">📅 Calendar Booking Assistant</h1>', unsafe_allow_html=True)

# Setup Instructions Section
st.markdown("## 🚀 First Time Setup Instructions")

st.markdown("""
<div class="p-4 border border-gray-300 rounded-lg bg-gray-50 my-4 text-black">
    <h3>📋 Grant Calendar Access to the Service Account</h3>
    <p>Before using the assistant, you must grant access to our service account. Follow these steps:</p>
    <ol>
        <li><strong>Go to Google Calendar</strong> (calendar.google.com)</li>
        <li><strong>Select your calendar</strong> from the left sidebar</li>
        <li><strong>Click "Settings and sharing"</strong></li>
        <li><strong>Scroll to "Share with specific people or groups"</strong></li>
        <li><strong>Click "Add people and groups"</strong></li>
        <li><strong>Add this email address:</strong></li>
    </ol>
    <div class="p-4 border border-gray-300 rounded-lg bg-gray-50 my-4 text-black">
               mohit-chat-model@careful-century-464605-b4.iam.gserviceaccount.com
    </div>
    <ol start="7">
        <li><strong>Set permission to "Make changes to events"</strong></li>
        <li><strong>Click "Send"</strong></li>
        <li><strong>(Optional) Copy your Calendar ID</strong> from the "Integrate calendar" section</li>
        <li><strong>Enter your Calendar ID</strong> in the sidebar (use "primary" for main calendar)</li>
        <li><strong>Start chatting!</strong></li>
    </ol>
    <p><em>⚠️ Without granting access, the assistant won't be able to read your calendar or book appointments.</em></p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Welcome to your AI-powered calendar booking assistant! I can help you:
- ✅ Check calendar availability
- 📋 Suggest available time slots  
- 📅 Book appointments
- 🔄 Handle rescheduling

Just start chatting below to book your next appointment!
""")

# Chat interface
st.subheader("💬 Chat")

# Display chat messages
chat_container = st.container()
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
                
                # Show booking confirmation if present
                if message.get("booking_made", False):
                    st.markdown("""
                    <div class="booking-success">
                        <h4>🎉 Booking Confirmed!</h4>
                        <p>Your appointment has been successfully added to your calendar.</p>
                    </div>
                    """, unsafe_allow_html=True)

# MODIFIED Chat input function
def send_message(message=None):
    # Use the provided message or get it from the session state
    user_message = message if message is not None else st.session_state.get("user_input", "")
    
    if user_message:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user", 
            "content": user_message
        })
        
        # Send to backend with calendar ID
        try:
            with st.spinner("🤔 Thinking..."):
                response = requests.post(
                    f"{st.session_state.backend_url}/chat",
                    json={
                        "message": user_message,
                        "session_id": st.session_state.session_id,
                        "calendar_id": st.session_state.user_calendar_id  # Include calendar ID
                    },
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                assistant_message = {
                    "role": "assistant",
                    "content": data["response"],
                    "booking_made": data.get("booking_made", False),
                    "booking_details": data.get("booking_details")
                }
                st.session_state.messages.append(assistant_message)
                
                if data.get("booking_made", False):
                    st.success("🎉 Appointment booked successfully!")
                    st.balloons()
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
        
        # Clear the input field ONLY if the call came from the text input
        if message is None:
            st.session_state.user_input = ""

# Input field
st.text_input(
    "Type your message here...",
    key="user_input",
    placeholder="e.g., 'I need to book a meeting for tomorrow at 2 PM'",
    on_change=send_message,
    label_visibility="collapsed"
)

# Example prompts
st.subheader("💭 Example Prompts")
col1, col2, col3 = st.columns(3)

with col1:
    st.button(  
        "📅 Book a meeting", 
        key="example1",
        on_click=send_message,
        args=("I need to book a meeting for tomorrow",)
    )

with col2:
    st.button(
        "🔍 Check availability", 
        key="example2",
        on_click=send_message,
        args=("What's my availability for this week",)
    )

with col3:
    st.button(
        "⏰ Schedule appointment", 
        key="example3",
        on_click=send_message,
        args=("Schedule a 1-hour appointment",)
    )

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>Powered by FastAPI, LangGraph, and Google Calendar API</p>
    <p>Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
