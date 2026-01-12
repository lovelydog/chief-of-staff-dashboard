"""Fetch Apple iCloud Calendar events via CalDAV"""
import json
import base64
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET


# CalDAV request body to fetch events
CALDAV_QUERY = '''<?xml version="1.0" encoding="utf-8" ?>
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


def parse_ical_event(ical_data):
    """Parse a single VEVENT from iCal format"""
    event = {}
    lines = ical_data.replace('\r\n ', '').split('\r\n')
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.split(';')[0]  # Remove parameters like DTSTART;TZID=...
            
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
    # Remove timezone suffix if present
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
            
            apple_id = data.get('apple_id', '')
            app_password = data.get('app_password', '')
            
            if not apple_id or not app_password:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Apple ID and app-specific password required"}).encode())
                return
            
            # CalDAV endpoint for iCloud
            caldav_url = "https://caldav.icloud.com"
            
            # Build auth header
            credentials = base64.b64encode(f"{apple_id}:{app_password}".encode()).decode()
            
            # Build time range
            now = datetime.utcnow()
            start = now.strftime('%Y%m%dT000000Z')
            end = (now + timedelta(days=7)).strftime('%Y%m%dT235959Z')
            
            # First, discover calendars (PROPFIND)
            propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
            <D:propfind xmlns:D="DAV:">
              <D:prop>
                <D:displayname/>
                <D:resourcetype/>
              </D:prop>
            </D:propfind>'''
            
            # Try to fetch from the default calendar path
            calendar_url = f"{caldav_url}/calendars/{apple_id}/calendar/"
            
            req = Request(
                calendar_url,
                data=CALDAV_QUERY.format(start=start, end=end).encode(),
                headers={
                    'Authorization': f'Basic {credentials}',
                    'Content-Type': 'application/xml',
                    'Depth': '1'
                },
                method='REPORT'
            )
            
            events = []
            
            try:
                with urlopen(req, timeout=10) as response:
                    xml_data = response.read().decode()
                    
                    # Parse XML response
                    root = ET.fromstring(xml_data)
                    
                    for response_elem in root.findall('.//{DAV:}response'):
                        cal_data = response_elem.find('.//{urn:ietf:params:xml:ns:caldav}calendar-data')
                        if cal_data is not None and cal_data.text:
                            ical = cal_data.text
                            
                            # Extract VEVENT
                            if 'VEVENT' in ical:
                                event = parse_ical_event(ical)
                                
                                if event.get('start'):
                                    start_dt = parse_datetime(event['start'])
                                    end_dt = parse_datetime(event.get('end', event['start']))
                                    
                                    events.append({
                                        "id": event.get('id', ''),
                                        "title": event.get('title', 'No Title'),
                                        "date": start_dt.strftime('%Y-%m-%d'),
                                        "start_time": start_dt.strftime('%H:%M'),
                                        "end_time": end_dt.strftime('%H:%M'),
                                        "duration_minutes": int((end_dt - start_dt).total_seconds() / 60),
                                        "organizer": event.get('organizer', ''),
                                        "attendees": [],
                                        "meeting_type": "external",
                                        "description": event.get('description', ''),
                                        "recurring": event.get('recurring', False),
                                        "source": "apple"
                                    })
                
            except HTTPError as e:
                if e.code == 401:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid Apple ID or app-specific password"}).encode())
                    return
                raise
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "events": events, 
                "source": "apple",
                "connected": True
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
