import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scope required to read/write calendar data
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def authenticate():
    """Handles OAuth2 authentication and token storage."""
    creds = None
    # Load existing token if it exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If no valid token, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Using the Desktop app client secret file
            flow = InstalledAppFlow.from_client_secrets_file(
                "tools/client_secret_483522683921-q3u8ngbtcdo0579eguv5cup0ltqtt4of.apps.googleusercontent.com.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for next time in token.json
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def schedule_meeting(service, title, start_time_iso, duration_hours=1):
    """
    Creates a meeting with title and start time in ISO format.
    
    Args:
        service: Google Calendar service instance
        title: Meeting title
        start_time_iso: Start time in ISO format (e.g., '2025-12-20T14:00:00')
        duration_hours: Duration in hours (default: 1)
    
    Returns:
        Event ID if successful, None otherwise
    """
    end_time_iso = (datetime.datetime.fromisoformat(start_time_iso) + 
                    datetime.timedelta(hours=duration_hours)).isoformat()

    event = {
        'summary': title,
        'start': {
            'dateTime': start_time_iso,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time_iso,
            'timeZone': 'UTC',
        },
    }

    try:
        event_result = service.events().insert(
            calendarId='primary', 
            body=event
        ).execute()
        print(f" Meeting created: {event_result.get('htmlLink')}")
        return event_result.get('id')
    except HttpError as error:
        print(f" An error occurred: {error}")
        return None


def list_meetings_by_date_range(service, start_time_iso, end_time_iso):
    """
    Lists all meetings within a specific date range.
    
    Args:
        service: Google Calendar service instance
        start_time_iso: Start time in ISO format (e.g., '2025-12-20T00:00:00')
        end_time_iso: End time in ISO format (e.g., '2025-12-25T23:59:59')
    
    Returns:
        List of events
    """
    print(f"\n📅 --- Meetings from {start_time_iso} to {end_time_iso} ---")
    
    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_time_iso + 'Z' if not start_time_iso.endswith('Z') else start_time_iso,
            timeMax=end_time_iso + 'Z' if not end_time_iso.endswith('Z') else end_time_iso,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        if not events:
            print("No meetings found in this date range.")
            return []
        
        print(f"\nFound {len(events)} meeting(s):\n")
        for idx, event in enumerate(events, 1):
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            print(f"{idx}. {event['summary']}")
            print(f"   � {start} to {end}")
            print(f"   🆔 ID: {event['id']}\n")
        
        return events
    except HttpError as error:
        print(f" An error occurred: {error}")
        return []


# ==================== MAIN EXECUTION ====================

# if __name__ == "__main__":
#     # Authenticate
#     service = authenticate()
    
#     # Example usage:
#     # 1. Schedule a meeting
#     schedule_meeting(service, "Team Standup", "2025-12-21T10:00:00", duration_hours=0.5)
    
#     # 2. List meetings in a date range
#     list_meetings_by_date_range(service, "2025-12-20T00:00:00", "2025-12-31T23:59:59")
    
#     print("Google Calendar tool ready. Use schedule_meeting() and list_meetings_by_date_range() functions.")