"""Google OAuth - Initiate login flow"""
import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlencode

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
REDIRECT_URI = os.environ.get('VERCEL_URL', 'http://localhost:3000')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not GOOGLE_CLIENT_ID:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "GOOGLE_CLIENT_ID not configured"}).encode())
            return
        
        # Build OAuth URL
        params = {
            'client_id': GOOGLE_CLIENT_ID,
            'redirect_uri': f"https://{REDIRECT_URI}/api/auth/google-callback" if REDIRECT_URI.startswith('http') == False else f"{REDIRECT_URI}/api/auth/google-callback",
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/calendar.readonly',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        # Redirect to Google
        self.send_response(302)
        self.send_header('Location', auth_url)
        self.end_headers()
