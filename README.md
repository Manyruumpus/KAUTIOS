# 📅 Calendar Booking Assistant

A conversational AI agent that assists users in booking appointments on Google Calendar through natural language chat interface.

## 🚀 Features

- **Natural Language Booking**: Book appointments through conversational chat
- **Calendar Integration**: Full Google Calendar integration with service account
- **Availability Checking**: Real-time calendar availability verification
- **Smart Suggestions**: AI-powered time slot recommendations
- **Modern UI**: Beautiful Streamlit chat interface
- **Session Management**: Persistent conversation sessions

## 🛠 Technology Stack

- **Backend**: Python FastAPI with LangGraph agent framework
- **Frontend**: Streamlit chat interface
- **AI/LLM**: Google Gemini 1.5 Flash with function calling
- **Calendar**: Google Calendar API with Service Account authentication
- **Deployment**: Railway/Render/Fly.io compatible

## 📋 Prerequisites

1. **Google Cloud Service Account**:
   - Create a Google Cloud project
   - Enable Google Calendar API
   - Create a Service Account with Calendar access
   - Download the service account JSON key file

2. **Google AI API Key**:
   - Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Ensure you have access to Gemini models

## 🔧 Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd calendar-booking-assistant
pip install -r requirements.txt
```

### 2. Google Calendar Setup

#### Create Service Account:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Go to "IAM & Admin" > "Service Accounts"
5. Create a new service account
6. Download the JSON key file
7. Rename it to `service-account-key.json` and place in project root

#### Share Calendar Access:
1. Open Google Calendar
2. Go to calendar settings
3. Share the calendar with your service account email
4. Grant "Make changes and manage sharing" permission

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
GOOGLE_API_KEY=your_google_ai_api_key
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
GOOGLE_CALENDAR_ID=primary
```

### 4. Run Locally

#### Start Backend:
```bash
cd backend
python main.py
# Backend will run on http://localhost:8000
```

#### Start Frontend:
```bash
cd frontend
streamlit run streamlit_app.py
# Frontend will run on http://localhost:8501
```

## 🌐 Deployment

### Option 1: Railway

1. Create account on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Deploy backend:
   - Create new service
   - Set environment variables
   - Deploy from `backend/` directory
4. Deploy frontend:
   - Create new service  
   - Set `BACKEND_URL` to your backend URL
   - Deploy from `frontend/` directory

### Option 2: Render

1. Create account on [Render](https://render.com)
2. Deploy backend as Web Service
3. Deploy frontend as Web Service
4. Set environment variables in dashboard

### Option 3: Fly.io

1. Install Fly CLI
2. Create `fly.toml` configuration
3. Deploy with `fly deploy`

### Environment Variables for Deployment

For deployment, set these environment variables:

```
GOOGLE_API_KEY=your_google_ai_api_key
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_CALENDAR_ID=primary
BACKEND_URL=https://your-backend-url.com
```

## 💬 Usage Examples

The assistant can handle natural language requests like:

- "I need to book a meeting for tomorrow at 2 PM"
- "Schedule a 1-hour appointment for next Monday"
- "What's my availability for this Friday?"
- "Book a client call for December 15th at 10 AM"
- "Find me a free slot this week for a team meeting"

## 🔧 API Endpoints

### Backend (FastAPI)

- `GET /` - Root endpoint
- `GET /health` - Health check with calendar status
- `POST /chat` - Chat with the booking agent

#### Chat Request:
```json
{
  "message": "I need to book a meeting",
  "session_id": "optional-session-id"
}
```

#### Chat Response:
```json
{
  "response": "I'd be happy to help you book a meeting...",
  "booking_made": false,
  "booking_details": null
}
```

## 🧠 Agent Capabilities

The LangGraph agent has access to these tools:

1. **check_calendar_availability**: Verify if a time slot is free
2. **suggest_available_slots**: Get available times for a date
3. **book_appointment**: Create calendar events

## 🔒 Security Notes

- Service account credentials should be kept secure
- Use environment variables for sensitive data
- Calendar access is limited to the shared calendar only
- API keys should never be committed to version control

## 🐛 Troubleshooting

### Common Issues:

1. **Calendar not connected**: 
   - Verify service account JSON is valid
   - Check calendar sharing permissions
   - Ensure Calendar API is enabled

2. **Google AI API errors**:
   - Verify API key is correct
   - Check account credits/billing (if applicable)
   - Ensure Gemini model access permissions

3. **Backend connection issues**:
   - Check if backend is running on correct port
   - Verify BACKEND_URL in frontend configuration
   - Check CORS settings

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions, please create an issue in the GitHub repository.
