#!/usr/bin/env python3
"""
Google Calendar Quick Add CLI
Create calendar events from natural language strings using Google Calendar API's quickAdd endpoint.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.auth.exceptions
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Authenticate and return Google Calendar API service"""
    creds = None
    token_path = os.path.expanduser('~/clawd/config/calendar_token.json')
    creds_path = os.path.expanduser('~/clawd/config/gcp-oauth.keys.json')
    
    # Token file stores user's access and refresh tokens
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f'⚠️  Could not load credentials: {e}')
            creds = None
    
    # If there are no (valid) credentials, let the user log in
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
        except google.auth.exceptions.RefreshError as e:
            print('❌ Refresh token invalid. Re-authentication required.')
            print('   Please run:')
            print('   cd ~/clawd && source venv/bin/activate && python3 scripts/calendar_manager.py --summary "Test" --date "2026-03-02" --start "10am" --end "10:30am"')
            print('   This will open a browser for OAuth approval.')
            raise SystemExit(1)
        except Exception as e:
            print(f'❌ Authentication failed: {e}')
            raise SystemExit(1)
        
        # Save the credentials for the next run
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f'⚠️  Could not save token: {e}')
    
    return build('calendar', 'v3', credentials=creds)

def quick_add_event(text, calendar_id='primary'):
    """
    Create an event using Google Calendar's quickAdd endpoint.
    Returns the created event dict or None on error.
    """
    try:
        service = get_calendar_service()
        result = service.events().quickAdd(
            calendarId=calendar_id,
            text=text
        ).execute()
        return result
    except HttpError as error:
        print(f'❌ QuickAdd failed: {error}')
        return None

def parse_date_time(date_str, time_str):
    """Parse date and time strings into datetime object (from calendar_manager.py)"""
    # This Friday
    today = datetime.now()
    if 'friday' in date_str.lower():
        days_ahead = 4 - today.weekday()  # Friday is 4
        if days_ahead <= 0:  # If today is Friday or later, get next Friday
            days_ahead += 7
        target_date = today + timedelta(days=days_ahead)
    else:
        # Try parsing as actual date
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Parse time
    hour, minute = map(int, time_str.replace('pm', '').replace('am', '').strip().split(':') if ':' in time_str else [time_str.replace('pm', '').replace('am', '').strip(), '0'])
    if 'pm' in time_str.lower() and hour != 12:
        hour += 12
    elif 'am' in time_str.lower() and hour == 12:
        hour = 0
    
    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

def create_event(summary, start_time, end_time, attendees=None, description=None, location=None, calendar_id='primary'):
    """
    Create a calendar event using structured insert (fallback).
    """
    try:
        service = get_calendar_service()
        
        # Convert datetime objects to ISO format if needed
        if isinstance(start_time, datetime):
            start_time = start_time.isoformat()
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()
        
        event = {
            'summary': summary,
            'description': description or '',
            'location': location or '',
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Phoenix',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Phoenix',
            },
        }
        
        # Add attendees if provided
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
            event['sendUpdates'] = 'all'  # Send invites
        
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"✅ Event created (structured fallback): {event.get('htmlLink')}")
        print(f"   Title: {summary}")
        print(f"   Time: {start_time} to {end_time}")
        if attendees:
            print(f"   Attendees: {', '.join(attendees)}")
        
        return event
    
    except HttpError as error:
        print(f'❌ Structured creation also failed: {error}')
        return None

def main():
    parser = argparse.ArgumentParser(description='Create a Google Calendar event from natural language')
    parser.add_argument('text', help='Natural language description of the event (e.g., "Lunch with John tomorrow at 1pm for 1 hour")')
    parser.add_argument('--calendar-id', default='primary', help='Calendar ID (default: primary)')
    parser.add_argument('--fallback', action='store_true', help='Force fallback to structured creation (skip quickAdd)')
    args = parser.parse_args()
    
    # Try quickAdd first unless --fallback is used
    if not args.fallback:
        try:
            event = quick_add_event(args.text, args.calendar_id)
            if event:
                print(f"✅ QuickAdd succeeded!")
                print(f"   Event: {event.get('summary', 'No title')}")
                print(f"   Link: {event.get('htmlLink', 'No link')}")
                print(f"   Start: {event.get('start', {}).get('dateTime', 'N/A')}")
                print(f"   End: {event.get('end', {}).get('dateTime', 'N/A')}")
                return
            else:
                print("❌ QuickAdd failed (no event returned).")
        except google.auth.exceptions.RefreshError:
            # Already handled in get_calendar_service, but catch here to avoid traceback
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error during QuickAdd: {e}")
            print("   Falling back to structured creation.")
    
    # If quickAdd failed or --fallback used, attempt structured fallback
    # For now, we don't have a robust natural language parser.
    # We'll simply output a message and suggest using calendar_manager.py
    print("❌ QuickAdd failed or not attempted. Structured fallback requires parsing.")
    print("   To create an event with explicit date/time, use:")
    print("   python3 ~/clawd/scripts/calendar_manager.py --summary 'Meeting' --date '2026-03-02' --start '3pm' --end '4pm'")
    sys.exit(1)

if __name__ == '__main__':
    main()