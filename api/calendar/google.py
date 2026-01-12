"""Fetch Google Calendar events"""
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from datetime import datetime, timedelta


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get token from query params or header
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            token = params.get('token', [None])[0]
            
            if not token:
                # Try Authorization header
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            
            if not token:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No access token provided"}).encode())
                return
            
            # Fetch calendar events
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=7)).isoformat() + 'Z'
            
            url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={time_min}&timeMax={time_max}&singleEvents=true&orderBy=startTime"
            
            req = Request(url, headers={'Authorization': f'Bearer {token}'})
            
            with urlopen(req) as response:
                data = json.loads(response.read())
            
            # Transform to our format
            events = []
            for item in data.get('items', []):
                start = item.get('start', {})
                end = item.get('end', {})
                
                # Handle all-day vs timed events
                if 'dateTime' in start:
                    start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                    start_date = start_dt.strftime('%Y-%m-%d')
                    start_time = start_dt.strftime('%H:%M')
                    end_time = end_dt.strftime('%H:%M')
                    duration = int((end_dt - start_dt).total_seconds() / 60)
                else:
                    start_date = start.get('date', '')
                    start_time = '00:00'
                    end_time = '23:59'
                    duration = 1440  # All day
                
                events.append({
                    "id": item.get('id', ''),
                    "title": item.get('summary', 'No Title'),
                    "date": start_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_minutes": duration,
                    "organizer": item.get('organizer', {}).get('email', ''),
                    "attendees": [a.get('email', '') for a in item.get('attendees', [])],
                    "meeting_type": "external",  # Default, can be improved
                    "description": item.get('description', ''),
                    "recurring": item.get('recurringEventId') is not None,
                    "source": "google"
                })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"events": events, "source": "google"}).encode())
            
        except HTTPError as e:
            error_body = e.read().decode()
            self.send_response(e.code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Google API error: {error_body}"}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
