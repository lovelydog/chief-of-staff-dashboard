"""Fetch Apple iCloud Calendar events via CalDAV"""
import json
import base64
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import ssl


ICLOUD_CALDAV_BASE = "https://caldav.icloud.com"


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


def resolve_url(base_url, path):
    """Resolve a relative path against a base URL"""
    if path.startswith('http://') or path.startswith('https://'):
        return path
    if path.startswith('/'):
        return f"{ICLOUD_CALDAV_BASE}{path}"
    return f"{base_url.rstrip('/')}/{path}"


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
            app_password = data.get('app_password', '').strip().replace(' ', '')  # Remove spaces
            
            if not apple_id or not app_password:
                self._send_error(400, "Apple ID and app-specific password required")
                return
            
            # Build auth header
            credentials = base64.b64encode(f"{apple_id}:{app_password}".encode()).decode()
            auth_header = f'Basic {credentials}'
            
            # Step 1: Discover principal and calendar home
            calendar_home = self._discover_calendar_home(auth_header, apple_id)
            
            if not calendar_home:
                self._send_error(404, "Could not discover calendar. Please verify your Apple ID.")
                return
            
            # Step 2: List calendars
            calendars = self._list_calendars(auth_header, calendar_home)
            
            # Step 3: Fetch events from all calendars
            all_events = []
            for cal_url in calendars:
                events = self._fetch_events(auth_header, cal_url)
                all_events.extend(events)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "events": all_events, 
                "source": "apple",
                "connected": True,
                "calendars_found": len(calendars),
                "message": f"Found {len(all_events)} events from {len(calendars)} calendar(s)"
            }).encode())
            
        except HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode()[:500]
            except:
                pass
            
            if e.code == 401:
                self._send_error(401, "Invalid credentials. Use the 16-character app-specific password (with or without dashes).")
            elif e.code == 404:
                self._send_error(404, f"Calendar not found at the expected location.")
            else:
                self._send_error(e.code, f"iCloud error {e.code}: {error_body}")
        except URLError as e:
            self._send_error(500, f"Connection error: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Error: {str(e)}")
    
    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())
    
    def _make_request(self, url, method, body, auth_header, depth='1'):
        """Make a CalDAV request with proper error handling"""
        # Ensure full URL
        if not url.startswith('http'):
            url = resolve_url(ICLOUD_CALDAV_BASE, url)
        
        req = Request(
            url,
            data=body.encode('utf-8') if body else None,
            headers={
                'Authorization': auth_header,
                'Content-Type': 'application/xml; charset=utf-8',
                'Depth': depth
            },
            method=method
        )
        
        ctx = ssl.create_default_context()
        return urlopen(req, timeout=15, context=ctx)
    
    def _discover_calendar_home(self, auth_header, apple_id):
        """Discover the user's calendar home URL"""
        
        # Method 1: Try direct calendar home path (most common)
        direct_paths = [
            f"/{apple_id}/calendars/",
            f"/calendars/home/{apple_id}/",
        ]
        
        for path in direct_paths:
            try:
                url = resolve_url(ICLOUD_CALDAV_BASE, path)
                propfind = '''<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:">
  <D:prop>
    <D:resourcetype/>
  </D:prop>
</D:propfind>'''
                with self._make_request(url, 'PROPFIND', propfind, auth_header, '0') as resp:
                    if resp.status == 207:
                        return url
            except HTTPError as e:
                if e.code not in [401, 404]:
                    continue
                if e.code == 401:
                    raise
            except:
                continue
        
        # Method 2: Discover via principal
        try:
            propfind = '''<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:current-user-principal/>
    <C:calendar-home-set/>
  </D:prop>
</D:propfind>'''
            
            with self._make_request(f"{ICLOUD_CALDAV_BASE}/", 'PROPFIND', propfind, auth_header, '0') as resp:
                xml_data = resp.read().decode()
                
                # Look for calendar-home-set or href
                import re
                home_match = re.search(r'calendar-home-set[^>]*>.*?<[^>]*href[^>]*>([^<]+)<', xml_data, re.IGNORECASE | re.DOTALL)
                if home_match:
                    return resolve_url(ICLOUD_CALDAV_BASE, home_match.group(1).strip())
                
                principal_match = re.search(r'current-user-principal[^>]*>.*?<[^>]*href[^>]*>([^<]+)<', xml_data, re.IGNORECASE | re.DOTALL)
                if principal_match:
                    principal_url = resolve_url(ICLOUD_CALDAV_BASE, principal_match.group(1).strip())
                    # Now get calendar-home-set from principal
                    return self._get_calendar_home_from_principal(auth_header, principal_url)
        except HTTPError as e:
            if e.code == 401:
                raise
        except:
            pass
        
        return None
    
    def _get_calendar_home_from_principal(self, auth_header, principal_url):
        """Get calendar home from principal URL"""
        try:
            propfind = '''<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <C:calendar-home-set/>
  </D:prop>
</D:propfind>'''
            
            with self._make_request(principal_url, 'PROPFIND', propfind, auth_header, '0') as resp:
                xml_data = resp.read().decode()
                import re
                match = re.search(r'<[^>]*href[^>]*>([^<]+)</[^>]*href>', xml_data, re.IGNORECASE)
                if match:
                    return resolve_url(ICLOUD_CALDAV_BASE, match.group(1).strip())
        except:
            pass
        return None
    
    def _list_calendars(self, auth_header, calendar_home):
        """List all calendars in the calendar home"""
        calendars = []
        
        try:
            propfind = '''<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:resourcetype/>
    <D:displayname/>
  </D:prop>
</D:propfind>'''
            
            with self._make_request(calendar_home, 'PROPFIND', propfind, auth_header, '1') as resp:
                xml_data = resp.read().decode()
                
                # Parse responses
                root = ET.fromstring(xml_data)
                for response in root.iter():
                    if response.tag.endswith('}response') or response.tag == 'response':
                        href = None
                        is_calendar = False
                        
                        for child in response.iter():
                            if child.tag.endswith('}href') or child.tag == 'href':
                                href = child.text
                            if child.tag.endswith('}calendar') or child.tag == 'calendar':
                                is_calendar = True
                        
                        if href and is_calendar:
                            calendars.append(resolve_url(ICLOUD_CALDAV_BASE, href.strip()))
        except:
            # Fallback: treat calendar_home as the calendar itself
            calendars.append(calendar_home)
        
        if not calendars:
            calendars.append(calendar_home)
        
        return calendars
    
    def _fetch_events(self, auth_header, calendar_url):
        """Fetch events from a calendar URL"""
        events = []
        
        # Build time range
        now = datetime.utcnow()
        start = now.strftime('%Y%m%dT000000Z')
        end = (now + timedelta(days=14)).strftime('%Y%m%dT235959Z')
        
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
        
        try:
            with self._make_request(calendar_url, 'REPORT', query, auth_header, '1') as resp:
                xml_data = resp.read().decode()
                root = ET.fromstring(xml_data)
                
                for elem in root.iter():
                    if 'calendar-data' in elem.tag and elem.text:
                        ical = elem.text
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
            if e.code not in [404, 403]:
                raise
        except:
            pass
        
        return events
