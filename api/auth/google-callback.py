"""Google OAuth Callback - Exchange code for tokens"""
import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import HTTPError

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
REDIRECT_URI = os.environ.get('VERCEL_URL', 'http://localhost:3000')


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse auth code from URL
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            code = params.get('code', [None])[0]
            error = params.get('error', [None])[0]
            
            if error:
                self._redirect_with_error(f"Google auth error: {error}")
                return
            
            if not code:
                self._redirect_with_error("No authorization code received")
                return
            
            # Exchange code for tokens
            callback_uri = f"https://{REDIRECT_URI}/api/auth/google-callback" if not REDIRECT_URI.startswith('http') else f"{REDIRECT_URI}/api/auth/google-callback"
            
            token_data = {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': callback_uri
            }
            
            req = Request(
                'https://oauth2.googleapis.com/token',
                data=json.dumps(token_data).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            with urlopen(req) as response:
                tokens = json.loads(response.read())
            
            access_token = tokens.get('access_token')
            refresh_token = tokens.get('refresh_token')
            
            # Store tokens (in a real app, save to database)
            # For now, redirect to frontend with success and token in URL fragment
            self.send_response(302)
            self.send_header('Location', f"/?google_connected=true&token={access_token}")
            self.end_headers()
            
        except HTTPError as e:
            error_body = e.read().decode()
            self._redirect_with_error(f"Token exchange failed: {error_body}")
        except Exception as e:
            self._redirect_with_error(str(e))
    
    def _redirect_with_error(self, error):
        self.send_response(302)
        self.send_header('Location', f"/?error={error}")
        self.end_headers()
