"""Fetch Apple iCloud Calendar events via CalDAV"""
import json
import base64
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import ssl


def parse_ical_event(ical_data):
    """Parse a single VEVENT from iCal format"""
    event = {}
    # Handle line continuations
    ical_data = ical_data.replace('\r\n ', '').replace('\n ', '')
    lines = ical_data.replace('\r\n', '\n').split('\n')
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.split(';')[0]  # Remove parameters
            
            if key == 'SUMMARY':
                event['title'] = value
            elif key == 'DTSTART':
                event['start'] = value
            elif key == 'DTEND':
                event['end'] = value
            elif key == 'DESCRIPTION':
                event['description'] = value
            elif key == 'UID':
                event['id'] = value
            elif key == 'ORGANIZER':
                event['organizer'] = value.replace('mailto:', '')
            elif key == 'RRULE':
                event['recurring'] = True
    
    return event


def parse_datetime(dt_str):
    """Parse iCal datetime string"""
    if not dt_str:
        return datetime.now()
    
    dt_str = dt_str.replace('Z', '')
    
    try:
        if 'T' in dt_str:
            return datetime.strptime(dt_str[:15], '%Y%m%dT%H%M%S')
        else:
            return datetime.strptime(dt_str[:8], '%Y%m%d')
    except:
        return datetime.now()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """Connect to Apple Calendar with credentials"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            apple_id = data.get('apple_id', '').strip()
            app_password = data.get('app_password', '').strip()
            
            if not apple_id or not app_password:
                self._send_error(400, "Apple ID and app-specific password required")
                return
            
            # Build auth header
            credentials = base64.b64encode(f"{apple_id}:{app_password}".encode()).decode()
            auth_header = f'Basic {credentials}'
            
            # Step 1: Discover principal URL
            principal_url = self._discover_principal(auth_header, apple_id)
            
            if not principal_url:
                # Fallback: try direct calendar home
                principal_url = f"https://caldav.icloud.com/{apple_id}/calendars/"
            
            # Step 2: Get calendar events
            events = self._fetch_events(auth_header, principal_url)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "events": events, 
                "source": "apple",
                "connected": True,
                "message": f"Found {len(events)} events"
            }).encode())
            
        except HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode()
            except:
                pass
            
            if e.code == 401:
                self._send_error(401, "Invalid Apple ID or app-specific password. Make sure you're using an app-specific password from appleid.apple.com")
            elif e.code == 404:
                self._send_error(404, "Calendar not found. Please check your Apple ID.")
            else:
                self._send_error(e.code, f"iCloud error: {e.code} - {error_body[:200]}")
        except URLError as e:
            self._send_error(500, f"Connection error: {str(e)}")
        except Exception as e:
            self._send_error(500, str(e))
    
    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())
    
    def _discover_principal(self, auth_header, apple_id):
        """Discover the user's calendar principal URL"""
        try:
            # Try the well-known CalDAV endpoint
            propfind = '''<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:">
  <D:prop>
    <D:current-user-principal/>
  </D:prop>
</D:propfind>'''
            
            req = Request(
                "https://caldav.icloud.com/",
                data=propfind.encode('utf-8'),
                headers={
                    'Authorization': auth_header,
                    'Content-Type': 'application/xml; charset=utf-8',
                    'Depth': '0'
                },
                method='PROPFIND'
            )
            
            ctx = ssl.create_default_context()
            with urlopen(req, timeout=10, context=ctx) as response:
                xml_data = response.read().decode()
                # Parse to find principal URL
                if 'href' in xml_data.lower():
                    # Simple extraction
                    import re
                    match = re.search(r'<[^>]*href[^>]*>([^<]+)</[^>]*href>', xml_data, re.IGNORECASE)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return None
    
    def _fetch_events(self, auth_header, calendar_url):
        """Fetch events from a calendar URL"""
        events = []
        
        # Build time range
        now = datetime.utcnow()
        start = now.strftime('%Y%m%dT000000Z')
        end = (now + timedelta(days=14)).strftime('%Y%m%dT235959Z')
        
        # CalDAV REPORT query
        query = f'''<?xml version="1.0" encoding="utf-8"?>
<C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:getetag/>
    <C:calendar-data/>
  </D:prop>
  <C:filter>
    <C:comp-filter name="VCALENDAR">
      <C:comp-filter name="VEVENT">
        <C:time-range start="{start}" end="{end}"/>
      </C:comp-filter>
    </C:comp-filter>
  </C:filter>
</C:calendar-query>'''
        
        req = Request(
            calendar_url,
            data=query.encode('utf-8'),
            headers={
                'Authorization': auth_header,
                'Content-Type': 'application/xml; charset=utf-8',
                'Depth': '1'
            },
            method='REPORT'
        )
        
        ctx = ssl.create_default_context()
        
        try:
            with urlopen(req, timeout=15, context=ctx) as response:
                xml_data = response.read().decode()
                
                # Parse XML response
                # Handle namespaces
                namespaces = {
                    'D': 'DAV:',
                    'C': 'urn:ietf:params:xml:ns:caldav'
                }
                
                root = ET.fromstring(xml_data)
                
                for resp in root.iter():
                    if 'calendar-data' in resp.tag and resp.text:
                        ical = resp.text
                        if 'VEVENT' in ical:
                            event = parse_ical_event(ical)
                            
                            if event.get('start'):
                                start_dt = parse_datetime(event['start'])
                                end_dt = parse_datetime(event.get('end', event['start']))
                                
                                duration = int((end_dt - start_dt).total_seconds() / 60)
                                if duration <= 0:
                                    duration = 60
                                
                                events.append({
                                    "id": event.get('id', ''),
                                    "title": event.get('title', 'No Title'),
                                    "date": start_dt.strftime('%Y-%m-%d'),
                                    "start_time": start_dt.strftime('%H:%M'),
                                    "end_time": end_dt.strftime('%H:%M'),
                                    "duration_minutes": duration,
                                    "organizer": event.get('organizer', ''),
                                    "attendees": [],
                                    "meeting_type": "external",
                                    "description": event.get('description', ''),
                                    "recurring": event.get('recurring', False),
                                    "source": "apple"
                                })
        except HTTPError as e:
            if e.code != 404:
                raise
        
        return events
