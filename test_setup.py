#!/usr/bin/env python3
"""
Test script to verify the calendar booking assistant setup with Gemini.
Run this to check if all dependencies and configurations are working.
"""

import os
import sys
from datetime import datetime
import json
import time 

# Import necessary classes at the top level
from langchain_google_genai import ChatGoogleGenerativeAI
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def test_imports():
    """Test if all required packages can be imported."""
    print("🔍 Testing package imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import langchain
        import langgraph
        print("✅ LangChain/LangGraph imported successfully")
    except ImportError as e:
        print(f"❌ LangChain/LangGraph import failed: {e}")
        return False
    
    # The imports for Google clients are already at the top,
    # so we just need to confirm the base packages are installed.
    try:
        import googleapiclient
        import google.oauth2
        print("✅ Google API client libraries imported successfully")
    except ImportError as e:
        print(f"❌ Google API client libraries import failed: {e}")
        return False
    
    try:
        import langchain_google_genai
        print("✅ Gemini/LangChain Google GenAI imported successfully")
    except ImportError as e:
        print(f"❌ Gemini/LangChain Google GenAI import failed: {e}")
        return False
    
    return True


def test_environment():
    """Test environment configuration."""
    print("\n🔍 Testing environment configuration...")
    
    # Check for .env file
    if os.path.exists('.env.example'):
        print("✅ .env file found (ensure it contains GOOGLE_API_KEY)")
        from dotenv import load_dotenv
        load_dotenv('.env.example')
    else:
        print("⚠️  .env file not found (using environment variables)")
    
    # Check Google API key (for Gemini)
    gemini_key = os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        print("✅ Google API key (for Gemini) configured")
    else:
        print("❌ Google API key (for Gemini) not found")
        return False
    
    # Check Google service account (for Calendar)
    service_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    service_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if service_file and os.path.exists(service_file):
        print("✅ Google service account file found")
    elif service_json:
        try:
            json.loads(service_json)
            print("✅ Google service account JSON configured")
        except json.JSONDecodeError:
            print("❌ Invalid Google service account JSON")
            return False
    else:
        print("❌ Google service account credentials not found")
        return False
    
    return True


def test_google_calendar():
    """Test Google Calendar connection."""
    print("\n🔍 Testing Google Calendar connection...")
    
    try:
        # Load credentials from service account
        service_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        service_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if service_file and os.path.exists(service_file):
            credentials = Credentials.from_service_account_file(
                service_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
        elif service_json:
            creds_info = json.loads(service_json)
            credentials = Credentials.from_service_account_info(
                creds_info,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
        else:
            print("❌ No Google credentials available for Calendar")
            return False
        
        # Build service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Test connection by getting calendar info
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        
        print(f"✅ Connected to calendar: {calendar.get('summary', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Google Calendar connection failed: {e}")
        return False


def test_gemini():
    """Test Gemini connection."""
    print("\n🔍 Testing Gemini connection...")
    
    try:
        print("Waiting 31 seconds to respect API rate limits...")
        time.sleep(31)
        
        print("Attempting to connect to Gemini...")
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)
        
        response = llm.invoke("Hello, this is a test. Please respond with 'Test successful!'")
        
        if "test successful" in response.content.lower():
            print("✅ Gemini connection successful")
            return True
        else:
            print(f"⚠️  Gemini responded but with unexpected content: {response.content}")
            return True
            
    except Exception as e:
        print(f"❌ Gemini connection failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Calendar Booking Assistant (Gemini Edition) - Setup Test\n")
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_environment():
        all_passed = False
    
    if os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE') or os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
        if not test_google_calendar():
            all_passed = False
    else:
        print("\n⚠️  Skipping Google Calendar test - credentials not configured")
    
    if os.getenv('GOOGLE_API_KEY'):
        if not test_gemini():
            all_passed = False
    else:
        print("\n⚠️  Skipping Gemini test - API key not configured")
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! Your setup is ready to go.")
        print("\nNext steps:")
        print("1. Start the backend: cd backend && python main.py")
        print("2. Start the frontend: cd frontend && streamlit run streamlit_app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Set up environment variables in a .env file")
        print("3. Configure Google Service Account credentials")
        print("4. Set up Google API key")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
