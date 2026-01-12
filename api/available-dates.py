"""Vercel Serverless Function for Available Dates API"""
import csv
import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path


def parse_calendar_csv():
    csv_path = Path(__file__).parent.parent / "calendar_sample.csv"
    meetings = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meetings.append({"date": row["date"]})
    return meetings


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            meetings = parse_calendar_csv()
            dates = sorted(set(m["date"] for m in meetings))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"dates": dates}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
