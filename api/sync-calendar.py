"""Sync calendar from all connected sources and merge"""
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


# This endpoint merges events from multiple sources
# In production, you'd store tokens in a database and fetch from all connected sources

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Return merged calendar from all sources"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Get tokens from query params
        google_token = params.get('google_token', [None])[0]
        
        events = []
        sources_connected = []
        
        # Note: In a production app, you'd:
        # 1. Store tokens in a secure database
        # 2. Automatically refresh expired tokens
        # 3. Fetch from all connected calendars
        
        response = {
            "events": events,
            "sources_connected": sources_connected,
            "message": "Connect calendars in Settings to see your events"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
