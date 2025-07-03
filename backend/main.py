from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
import pytz 
import dateparser
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
import json
from dotenv import load_dotenv
import codecs
import threading
import re

# Load environment variables from .env file in the current directory
load_dotenv()

# --- Configuration ---
USER_TIMEZONE = "Asia/Kolkata"
tz = pytz.timezone(USER_TIMEZONE)
WORK_HOURS_START = 9
WORK_HOURS_END = 17
SEARCH_LIMIT_DAYS = 30

# --- Thread-local storage for session-specific data ---
session_local = threading.local()

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Calendar Booking Agent API",
    description="AI-powered calendar booking assistant",
    version="2.0.0"
)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",      # Local Streamlit
        "https://*.streamlit.app",    # Streamlit Cloud  
        "https://*.onrender.com",     # Your frontend on Render
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    calendar_id: Optional[str] = "primary"

class ChatResponse(BaseModel):
    response: str
    booking_made: bool = False
    booking_details: Optional[Dict] = None

# --- Google Calendar Service ---
class GoogleCalendarService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.initialize_service()
    
    def initialize_service(self):
        try:
            # Load credentials from file or environment variable
            creds_file_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
            
            if creds_file_path and os.path.exists(creds_file_path):
                self.credentials = Credentials.from_service_account_file(
                    creds_file_path, scopes=['https://www.googleapis.com/auth/calendar']
                )
            elif os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
                creds_json_str = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
                creds_info = json.loads(creds_json_str)
                creds_info['private_key'] = codecs.decode(creds_info['private_key'], 'unicode_escape')
                self.credentials = Credentials.from_service_account_info(
                    creds_info, scopes=['https://www.googleapis.com/auth/calendar']
                )
            
            if self.credentials:
                self.service = build('calendar', 'v3', credentials=self.credentials)
                print("✅ Google Calendar service initialized successfully.")
            else:
                print("⚠️ Warning: Google Calendar credentials not found.")
        except Exception as e:
            print(f"❌ Error initializing Google Calendar service: {e}")
    
    def check_availability(self, start_time_utc: datetime, end_time_utc: datetime, calendar_id: str):
        """Check if a time slot is available in the specified calendar"""
        if not self.service: 
            return False
        
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time_utc.isoformat(),
                timeMax=end_time_utc.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return len(events_result.get('items', [])) == 0
        except Exception as e:
            print(f"Error checking availability for calendar {calendar_id}: {e}")
            return False

    def create_event(self, title: str, start_time_utc: datetime, end_time_utc: datetime, calendar_id: str, description: str = ""):
        """Create an event in the specified calendar"""
        if not self.service: 
            return None
        
        try:
            event = {
                'summary': title, 
                'description': description,
                'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
            }
            return self.service.events().insert(calendarId=calendar_id, body=event).execute()
        except Exception as e:
            print(f"Error creating event in calendar {calendar_id}: {e}")
            return None

    def create_recurring_event(self, title: str, start_time_utc: datetime, end_time_utc: datetime, 
                              calendar_id: str, recurrence_rule: str, description: str = ""):
        """Create a recurring event in the specified calendar"""
        if not self.service: 
            return None
        
        try:
            event = {
                'summary': title, 
                'description': description,
                'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
                'recurrence': [recurrence_rule]
            }
            return self.service.events().insert(calendarId=calendar_id, body=event).execute()
        except Exception as e:
            print(f"Error creating recurring event in calendar {calendar_id}: {e}")
            return None

    def create_multiple_events(self, title: str, event_times: List[Dict], calendar_id: str, description: str = ""):
        """Create multiple individual events"""
        if not self.service:
            return []
        
        created_events = []
        failed_events = []
        
        for event_time in event_times:
            start_utc = event_time['start_utc']
            end_utc = event_time['end_utc']
            
            # Check availability first
            if not self.check_availability(start_utc, end_utc, calendar_id):
                failed_events.append({
                    'date': event_time['date_str'],
                    'reason': 'Time slot not available'
                })
                continue
            
            event = self.create_event(title, start_utc, end_utc, calendar_id, description)
            if event:
                created_events.append({
                    'event_id': event.get('id'),
                    'date': event_time['date_str'],
                    'link': event.get('htmlLink')
                })
            else:
                failed_events.append({
                    'date': event_time['date_str'],
                    'reason': 'Failed to create event'
                })
        
        return created_events, failed_events

    def suggest_time_slots(self, preferred_date_local: datetime, duration_minutes: int, calendar_id: str):
        """Suggest available time slots for a given date in the specified calendar"""
        if not self.service: 
            return []
        
        start_of_day = preferred_date_local.replace(hour=WORK_HOURS_START, minute=0, second=0, microsecond=0)
        end_of_day = preferred_date_local.replace(hour=WORK_HOURS_END, minute=0, second=0, microsecond=0)
        
        suggestions = []
        current_time_local = start_of_day
        
        while current_time_local + timedelta(minutes=duration_minutes) <= end_of_day:
            end_time_local = current_time_local + timedelta(minutes=duration_minutes)
            start_utc = current_time_local.astimezone(pytz.utc)
            end_utc = end_time_local.astimezone(pytz.utc)

            if self.check_availability(start_utc, end_utc, calendar_id):
                suggestions.append({
                    'display': f"{current_time_local.strftime('%I:%M %p')} - {end_time_local.strftime('%I:%M %p')}"
                })
            
            current_time_local += timedelta(minutes=30)
            if len(suggestions) >= 5: 
                break
            
        return suggestions

    def validate_calendar_access(self, calendar_id: str):
        """Validate if the service account has access to the specified calendar"""
        if not self.service:
            return False
        
        try:
            # Try to get calendar metadata
            calendar = self.service.calendars().get(calendarId=calendar_id).execute()
            return True
        except Exception as e:
            print(f"Calendar access validation failed for {calendar_id}: {e}")
            return False

# --- Initialize Calendar Service ---
calendar_service = GoogleCalendarService()

# --- Helper Functions ---
def parse_time(time_str: str) -> Optional[datetime]:
    """Parse natural language date/time into a timezone-aware datetime object"""
    parsed_date = dateparser.parse(
        time_str, 
        settings={
            'PREFER_DATES_FROM': 'future', 
            'TIMEZONE': USER_TIMEZONE, 
            'RETURN_AS_TIMEZONE_AWARE': True
        }
    )
    if parsed_date and parsed_date.tzinfo is None:
        return tz.localize(parsed_date)
    return parsed_date

def get_current_calendar_id():
    """Get the calendar ID for the current session"""
    return getattr(session_local, 'calendar_id', 'primary')

def set_current_calendar_id(calendar_id: str):
    """Set the calendar ID for the current session"""
    session_local.calendar_id = calendar_id

def parse_weekdays(weekdays_str: str) -> List[int]:
    """Parse weekday names to weekday numbers (0=Monday, 6=Sunday)"""
    weekday_mapping = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
    }
    
    weekdays = []
    for day in weekdays_str.lower().split(','):
        day = day.strip()
        if day in weekday_mapping:
            weekdays.append(weekday_mapping[day])
    
    return weekdays

def generate_recurring_dates(start_date: datetime, end_date: datetime, weekdays: List[int],
                           start_time_str: str, end_time_str: str) -> List[Dict]:
    """Generate list of recurring event dates and times"""
    events = []
    current_date = start_date.date()
    end_date_only = end_date.date()
    
    # Parse start and end times
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.strptime(end_time_str, '%H:%M').time()
    
    while current_date <= end_date_only:
        if current_date.weekday() in weekdays:
            # Create datetime objects for this occurrence
            start_datetime = tz.localize(datetime.combine(current_date, start_time))
            end_datetime = tz.localize(datetime.combine(current_date, end_time))
            
            events.append({
                'start_utc': start_datetime.astimezone(pytz.utc),
                'end_utc': end_datetime.astimezone(pytz.utc),
                'date_str': current_date.strftime('%A, %B %d, %Y'),
                'time_str': f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            })
        
        current_date += timedelta(days=1)
    
    return events

# --- Agent Tools (Updated to include recurring appointments) ---
@tool
def find_next_available_slot(duration_minutes: int = 60) -> str:
    """
    Finds the very next available time slot starting from right now.
    Use this for general queries like 'When are you free next?' or 'Find me the soonest opening'.
    Args:
        duration_minutes: The required duration of the meeting in minutes. Defaults to 60.
    """
    if not calendar_service.service:
        return "Error: Calendar service is not connected."
    
    calendar_id = get_current_calendar_id()
    
    # Validate calendar access
    if not calendar_service.validate_calendar_access(calendar_id):
        return f"Error: Cannot access calendar '{calendar_id}'. Please ensure the service account has been granted access to your calendar."
    
    start_search_local = datetime.now(tz)
    current_time = start_search_local
    
    while current_time < start_search_local + timedelta(days=SEARCH_LIMIT_DAYS):
        # Round to next 30-minute interval
        if current_time.minute not in [0, 30]:
            if current_time.minute < 30: 
                current_time = current_time.replace(minute=30, second=0, microsecond=0)
            else: 
                current_time = (current_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        # Skip weekends and outside work hours
        if current_time.weekday() >= 5 or not (WORK_HOURS_START <= current_time.hour < WORK_HOURS_END):
            current_time = (current_time + timedelta(days=1)).replace(hour=WORK_HOURS_START, minute=0)
            continue

        end_time = current_time + timedelta(minutes=duration_minutes)
        
        # Check if meeting would end after work hours
        if end_time.hour > WORK_HOURS_END or (end_time.hour == WORK_HOURS_END and end_time.minute > 0):
             current_time = (current_time + timedelta(days=1)).replace(hour=WORK_HOURS_START, minute=0)
             continue

        # Check availability using user's calendar ID
        if calendar_service.check_availability(current_time.astimezone(pytz.utc), end_time.astimezone(pytz.utc), calendar_id):
            return f"Success! The next available {duration_minutes}-minute slot is on {current_time.strftime('%A, %B %d at %I:%M %p %Z')}."
            
        current_time += timedelta(minutes=30)
        
    return f"I'm sorry, I couldn't find any available {duration_minutes}-minute slots in the next {SEARCH_LIMIT_DAYS} days."

@tool
def suggest_available_slots(date: str, duration_minutes: int = 60) -> str:
    """
    Suggests available time slots for a specific given date.
    Use this when the user asks for availability on a particular day (e.g., 'tomorrow', 'July 5th').
    Args:
        date: The desired date in natural language (e.g., 'tomorrow', 'next Friday', 'July 5th').
        duration_minutes: The duration of the meeting in minutes. Defaults to 60.
    """
    if not calendar_service.service: 
        return "Error: Calendar service is not connected."
    
    calendar_id = get_current_calendar_id()
    
    # Validate calendar access
    if not calendar_service.validate_calendar_access(calendar_id):
        return f"Error: Cannot access calendar '{calendar_id}'. Please ensure the service account has been granted access to your calendar."
    
    target_date_local = parse_time(date)
    if not target_date_local: 
        return f"Error: I couldn't understand the date '{date}'."

    suggestions = calendar_service.suggest_time_slots(target_date_local, duration_minutes, calendar_id)
    
    if suggestions:
        slots_text = "\n".join([f"- {slot['display']}" for slot in suggestions])
        return f"I found a few slots for {target_date_local.strftime('%A, %B %d')}:\n{slots_text}\nWhich one works for you?"
    
    return f"Sorry, no available {duration_minutes}-minute slots on {target_date_local.strftime('%A, %B %d')}."

@tool
def book_appointment(title: str, start_time: str, duration_minutes: int = 60, description: str = "") -> str:
    """
    Books an appointment in the calendar after all details are confirmed.
    Only use this tool when you have the title, start time, and duration confirmed by the user.
    Args:
        title: The title or subject of the appointment.
        start_time: The start time in natural language (e.g., 'tomorrow at 3 PM', 'next Monday at 10am').
        duration_minutes: The duration of the meeting in minutes. Defaults to 60.
        description: An optional description for the appointment.
    """
    if not calendar_service.service: 
        return json.dumps({"error": "Calendar service is not connected."})
    
    calendar_id = get_current_calendar_id()
    
    # Validate calendar access
    if not calendar_service.validate_calendar_access(calendar_id):
        return json.dumps({"error": f"Cannot access calendar '{calendar_id}'. Please ensure the service account has been granted access to your calendar."})
    
    start_time_local = parse_time(start_time)
    if not start_time_local: 
        return json.dumps({"error": f"I couldn't understand the time '{start_time}'."})

    end_time_local = start_time_local + timedelta(minutes=duration_minutes)
    
    # Final availability check
    if not calendar_service.check_availability(start_time_local.astimezone(pytz.utc), end_time_local.astimezone(pytz.utc), calendar_id):
        return json.dumps({"error": "Sorry, that time is no longer available."})
    
    # Create the event
    event = calendar_service.create_event(
        title, 
        start_time_local.astimezone(pytz.utc), 
        end_time_local.astimezone(pytz.utc), 
        calendar_id, 
        description
    )
    
    if event:
        return json.dumps({
            "success": True, 
            "message": f"Great! I've booked '{title}' for you.", 
            "details": {
                "title": title, 
                "time_range_local": f"{start_time_local.strftime('%A, %B %d at %I:%M %p')} - {end_time_local.strftime('%I:%M %p')} ({USER_TIMEZONE})", 
                "google_calendar_link": event.get('htmlLink'),
                "event_id": event.get('id'),
                "calendar_id": calendar_id
            }
        })
    
    return json.dumps({"error": "Error creating the event on Google Calendar."})

@tool
def book_recurring_appointment(title: str, weekdays: str, start_time: str, end_time: str, 
                             end_date: str, description: str = "") -> str:
    """
    Books recurring appointments in the calendar for specific weekdays until an end date.
    Use this when the user wants to book regular appointments on specific days of the week.
    Args:
        title: The title or subject of the recurring appointment.
        weekdays: Comma-separated list of weekdays (e.g., 'tuesday,thursday,friday' or 'mon,wed,fri').
        start_time: The start time in HH:MM format (e.g., '16:15' or '14:30').
        end_time: The end time in HH:MM format (e.g., '18:00' or '15:30').
        end_date: The end date in natural language (e.g., 'July 11th', '2025-07-11').
        description: An optional description for the appointments.
    """
    if not calendar_service.service: 
        return json.dumps({"error": "Calendar service is not connected."})
    
    calendar_id = get_current_calendar_id()
    
    # Validate calendar access
    if not calendar_service.validate_calendar_access(calendar_id):
        return json.dumps({"error": f"Cannot access calendar '{calendar_id}'. Please ensure the service account has been granted access to your calendar."})
    
    # Parse end date
    end_date_parsed = parse_time(end_date)
    if not end_date_parsed:
        return json.dumps({"error": f"I couldn't understand the end date '{end_date}'."})
    
    # Parse weekdays
    weekday_numbers = parse_weekdays(weekdays)
    if not weekday_numbers:
        return json.dumps({"error": f"I couldn't understand the weekdays '{weekdays}'. Please use format like 'tuesday,thursday,friday'."})
    
    # Validate time format
    try:
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
    except ValueError:
        return json.dumps({"error": "Please use HH:MM format for times (e.g., '16:15', '18:00')."})
    
    # Generate recurring dates
    start_date = datetime.now(tz)
    recurring_events = generate_recurring_dates(
        start_date, end_date_parsed, weekday_numbers, start_time, end_time
    )
    
    if not recurring_events:
        return json.dumps({"error": "No matching dates found for the specified weekdays and date range."})
    
    # Create multiple events
    created_events, failed_events = calendar_service.create_multiple_events(
        title, recurring_events, calendar_id, description
    )
    
    if created_events:
        success_count = len(created_events)
        total_count = len(recurring_events)
        
        # Create summary message
        weekday_names = [['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][i] for i in weekday_numbers]
        summary = f"Successfully booked {success_count} out of {total_count} recurring appointments for '{title}'"
        
        details = {
            "title": title,
            "weekdays": weekday_names,
            "time_range": f"{start_time_obj.strftime('%I:%M %p')} - {end_time_obj.strftime('%I:%M %p')} ({USER_TIMEZONE})",
            "end_date": end_date_parsed.strftime('%B %d, %Y'),
            "created_events": created_events,
            "failed_events": failed_events,
            "calendar_id": calendar_id
        }
        
        if failed_events:
            summary += f". {len(failed_events)} appointments couldn't be created due to conflicts."
        
        return json.dumps({
            "success": True,
            "message": summary,
            "details": details
        })
    
    return json.dumps({"error": "Failed to create any recurring appointments. Please check for time conflicts."})

@tool
def validate_calendar_setup(calendar_id: str = None) -> str:
    """
    Validates if the calendar setup is correct and the service account has proper access.
    Args:
        calendar_id: The calendar ID to validate. Uses current session calendar if not provided.
    """
    if not calendar_service.service:
        return "Error: Calendar service is not connected. Please check service account credentials."
    
    if calendar_id is None:
        calendar_id = get_current_calendar_id()
    
    if calendar_service.validate_calendar_access(calendar_id):
        return f"✅ Calendar access validated successfully for '{calendar_id}'. You're all set!"
    else:
        return f"❌ Cannot access calendar '{calendar_id}'. Please ensure you've granted access to: mohit-chat-model@careful-century-464605-b4.iam.gserviceaccount.com with 'Make changes to events' permission."

# --- LangGraph Agent Setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    temperature=0.2, 
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

tools = [find_next_available_slot, suggest_available_slots, book_appointment, book_recurring_appointment, validate_calendar_setup]
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict): 
    messages: Annotated[list, add_messages]

def agent_node(state: AgentState): 
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def tool_node(state: AgentState):
    tool_calls = state["messages"][-1].tool_calls
    tool_outputs = []
    tool_map = {tool.name: tool for tool in tools}
    
    for call in tool_calls:
        if call["name"] in tool_map:
            try: 
                output = tool_map[call["name"]].invoke(call["args"])
            except Exception as e: 
                output = f"Error running tool {call['name']}: {e}"
            tool_outputs.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
    
    return {"messages": tool_outputs}

def should_continue(state: AgentState):
    return "tools" if state["messages"][-1].tool_calls else END

# Build the workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")
agent = workflow.compile()

# System prompt for the agent
system_prompt = f"""You are a friendly and highly capable calendar booking assistant for a user in {USER_TIMEZONE}.

Current date and time: {datetime.now(tz).strftime('%A, %B %d, %Y, %I:%M %p %Z')}

Your capabilities include:
1. **Single appointments**: Use `book_appointment` for one-time events
2. **Recurring appointments**: Use `book_recurring_appointment` for regular events on specific weekdays
3. **Availability checking**: Use `find_next_available_slot` or `suggest_available_slots`
4. **Calendar validation**: Use `validate_calendar_setup` for troubleshooting

For recurring appointments, you can handle requests like:
- "Book a meeting every Tuesday and Thursday from 2 PM to 4 PM until July 15th"
- "Schedule eco423 class every Tuesday, Thursday, and Friday from 4:15 PM to 6:00 PM till July 11th"

Your process:
1. Listen carefully to understand if the user wants a single or recurring appointment
2. For recurring appointments, extract:
   - Title/subject
   - Weekdays (convert to standard format: tuesday,thursday,friday)
   - Start time (convert to 24-hour format: 16:15)
   - End time (convert to 24-hour format: 18:00)
   - End date (natural language is fine)
3. Always confirm details before booking
4. Use the appropriate tool based on the request type
5. Provide helpful feedback about successful bookings and any conflicts

Remember to be conversational, helpful, and ensure the user confirms all details before creating calendar events.
"""

initial_messages = [AIMessage(content=system_prompt)]

# --- Session Storage ---
sessions = {}

# --- API Endpoints ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    calendar_id = request.calendar_id or "primary"
    
    # Set the calendar ID for this request context
    set_current_calendar_id(calendar_id)
    
    # Initialize session if it doesn't exist
    if session_id not in sessions: 
        sessions[session_id] = {
            "messages": initial_messages.copy(),
            "calendar_id": calendar_id
        }
    
    # Update calendar_id for this session
    sessions[session_id]["calendar_id"] = calendar_id
    
    # Add user message to conversation history
    sessions[session_id]["messages"].append(HumanMessage(content=request.message))
    
    try:
        # Invoke the agent
        result = agent.invoke({"messages": sessions[session_id]["messages"]})
        
        final_message = result["messages"][-1]
        response_content = final_message.content
        
        # Update session with full conversation
        sessions[session_id]["messages"] = result["messages"]

        # Check if a booking was made
        booking_made = False
        booking_details = None
        tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
        
        if tool_messages:
            try:
                tool_data = json.loads(tool_messages[-1].content)
                if tool_data.get("success"):
                    booking_made = True
                    booking_details = tool_data.get("details")
                    response_content = tool_data.get("message", response_content)
            except (json.JSONDecodeError, TypeError): 
                pass

        return ChatResponse(
            response=response_content, 
            booking_made=booking_made, 
            booking_details=booking_details
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "calendar_service": calendar_service.service is not None,
        "timezone": USER_TIMEZONE,
        "current_time": datetime.now(tz).isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Calendar Booking Agent API is running!",
        "status": "healthy",
        "version": "2.0.0",
            # "features": ["single_appointments", "recurring_appointments", "availability_checking"],
            # "docs": "/docs"
    }

@app.get("/instructions")
async def get_instructions():
    """Endpoint to provide setup instructions for new users"""
    return {
        "service_account_email": "mohit-chat-model@careful-century-464605-b4.iam.gserviceaccount.com",
        "instructions": [
            "1. Go to Google Calendar (calendar.google.com)",
            "2. Click on your calendar in the left sidebar",
            "3. Select 'Settings and sharing'", 
            "4. Scroll to 'Share with specific people or groups'",
            "5. Add: mohit-chat-model@careful-century-464605-b4.iam.gserviceaccount.com",
            "6. Set permission to 'Make changes to events'",
            "7. (Optional) Get your Calendar ID from 'Integrate calendar' section",
            "8. Use 'primary' for your main calendar or paste your specific Calendar ID",
            "9. Start using the assistant!"
        ],
        "recurring_examples": [
            "Book a meeting every Tuesday and Thursday from 2 PM to 4 PM until July 15th",
            "Schedule eco423 class every Tuesday, Thursday, and Friday from 4:15 PM to 6:00 PM till July 11th",
            "Set up weekly team meeting every Monday from 10 AM to 11 AM until end of month"
        ]
    }

@app.post("/validate-calendar")
async def validate_calendar_endpoint(request: dict):
    """Endpoint to validate calendar access"""
    calendar_id = request.get("calendar_id", "primary")
    
    if not calendar_service.service:
        return {
            "valid": False,
            "message": "Calendar service is not connected. Please check service account credentials."
        }
    
    is_valid = calendar_service.validate_calendar_access(calendar_id)
    
    return {
        "valid": is_valid,
        "calendar_id": calendar_id,
        "message": "Calendar access validated successfully." if is_valid else 
                   f"Cannot access calendar '{calendar_id}'. Please ensure you've granted access to the service account."
    }

# --- Main Execution Block ---
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting Calendar Booking Agent API...")
    print(f"📅 Timezone: {USER_TIMEZONE}")
    print(f"⏰ Work Hours: {WORK_HOURS_START}:00 - {WORK_HOURS_END}:00")
    print(f"🔑 Service Account: mohit-chat-model@careful-century-464605-b4.iam.gserviceaccount.com")
    print(f"🔄 Features: Single & Recurring Appointments")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
