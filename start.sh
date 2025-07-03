#!/bin/bash

# Calendar Booking Assistant - Startup Script
echo "🚀 Starting Calendar Booking Assistant..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Install dependencies if not already installed
echo "📦 Checking dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your credentials before continuing."
    echo "   Required: DEEPSEEK_API_KEY, Google Service Account credentials"
    exit 1
fi

# Run tests
echo "🧪 Running setup tests..."
python test_setup.py
if [ $? -ne 0 ]; then
    echo "❌ Setup tests failed. Please fix the issues above."
    exit 1
fi

# Function to start backend
start_backend() {
    echo "🔧 Starting FastAPI backend on port 8000..."
    cd backend
    python main.py &
    BACKEND_PID=$!
    cd ..
    echo "Backend PID: $BACKEND_PID"
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting Streamlit frontend on port 8501..."
    cd frontend
    streamlit run streamlit_app.py --server.port=8501 &
    FRONTEND_PID=$!
    cd ..
    echo "Frontend PID: $FRONTEND_PID"
}

# Function to cleanup processes
cleanup() {
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "Frontend stopped"
    fi
    exit 0
}

# Set up trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start services
start_backend
sleep 3  # Give backend time to start

start_frontend
sleep 3  # Give frontend time to start

# Display access information
echo ""
echo "🎉 Services are running!"
echo "📍 Backend API: http://localhost:8000"
echo "📍 Frontend UI: http://localhost:8501"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait