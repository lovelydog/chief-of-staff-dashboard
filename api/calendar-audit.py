"""Vercel Serverless Function for Calendar Audit API"""
import csv
import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
import re


# OKR Keywords for matching
OKR_KEYWORDS = {
    "platform_modernization": [
        "kubernetes", "k8s", "migration", "deployment", "uptime", 
        "infrastructure", "platform", "devops", "ci/cd", "architecture"
    ],
    "engineering_team": [
        "hire", "hiring", "interview", "staff engineer", "principal",
        "attrition", "mentorship", "mentor", "career", "growth", "1:1"
    ],
    "ai_ml_integration": [
        "ai", "ml", "machine learning", "artificial intelligence",
        "data science", "model", "poc", "search"
    ]
}

MEETING_TYPE_SCORES = {
    "architecture": 95, "strategic_planning": 90, "board_prep": 90,
    "one_on_one": 85, "hiring": 80, "interview": 75, "incident_review": 85,
    "external": 70, "design_review": 60, "sprint_ceremony": 30,
    "standup": 25, "status_update": 20, "vendor_demo": 40, "adhoc": 35, "prep": 50, "strategic": 80,
}

JUNIOR_INDICATORS = ["junior", "intern", "new hire", "onboarding", "coffee chat"]
SENIOR_INDICATORS = ["staff", "principal", "director", "vp", "cto", "ceo", "cfo", "board", "investor"]


def parse_calendar_csv():
    """Parse calendar CSV file."""
    csv_path = Path(__file__).parent.parent / "calendar_sample.csv"
    meetings = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meeting = {
                "id": int(row["id"]),
                "title": row["title"],
                "date": row["date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "duration_minutes": int(row["duration_minutes"]),
                "organizer": row["organizer"],
                "attendees": [a.strip() for a in row["attendees"].split(";")],
                "meeting_type": row["meeting_type"],
                "description": row["description"],
                "recurring": row["recurring"].lower() == "true"
            }
            meetings.append(meeting)
    return meetings


def find_okr_relevance(meeting):
    relevant_okrs = []
    text_to_search = f"{meeting['title']} {meeting['description']} {meeting['meeting_type']}".lower()
    if any(kw in text_to_search for kw in OKR_KEYWORDS["platform_modernization"]):
        relevant_okrs.append("Platform Modernization")
    if any(kw in text_to_search for kw in OKR_KEYWORDS["engineering_team"]):
        relevant_okrs.append("Build World-Class Engineering Team")
    if any(kw in text_to_search for kw in OKR_KEYWORDS["ai_ml_integration"]):
        relevant_okrs.append("AI/ML Integration")
    return relevant_okrs


def calculate_alignment_score(meeting):
    flags = []
    text_lower = f"{meeting['title']} {meeting['description']}".lower()
    attendees_lower = " ".join(meeting["attendees"]).lower()
    
    base_type_score = MEETING_TYPE_SCORES.get(meeting["meeting_type"], 40)
    type_score = base_type_score
    
    okr_relevance = find_okr_relevance(meeting)
    okr_score = min(100, 70 + len(okr_relevance) * 15) if okr_relevance else 30
    if not okr_relevance:
        flags.append("No clear OKR alignment detected")
    
    attendee_score = 60
    is_junior_activity = any(ind in text_lower for ind in JUNIOR_INDICATORS)
    is_senior_activity = any(ind in text_lower or ind in attendees_lower for ind in SENIOR_INDICATORS)
    
    if is_junior_activity and not is_senior_activity:
        attendee_score = 25
        flags.append(f"CTO attending junior-level activity: '{meeting['title']}'")
    elif is_senior_activity:
        attendee_score = 90
    
    if meeting["meeting_type"] == "design_review" and is_junior_activity:
        type_score = 20
        flags.append("Design review should be delegated to Engineering Manager")
    if meeting["meeting_type"] == "interview" and is_junior_activity:
        type_score = 25
        flags.append("Interview for junior role - delegate to hiring manager")
    if meeting["meeting_type"] == "vendor_demo":
        if "25k" in text_lower or "10k" in text_lower:
            type_score = 20
            flags.append("Vendor demo for tool under $50K threshold - delegate")
        elif "200k" in text_lower or "100k" in text_lower:
            type_score = 70
    if meeting["meeting_type"] == "status_update":
        flags.append("Status updates should be asynchronous - consider declining")
        type_score = 15
    if meeting["meeting_type"] == "sprint_ceremony":
        flags.append("Sprint ceremony - CTO attendance rarely necessary")
    
    strategic_types = ["architecture", "strategic_planning", "board_prep", "hiring"]
    enablement_types = ["one_on_one", "interview", "mentorship"]
    admin_types = ["standup", "status_update", "prep", "adhoc"]
    
    if meeting["meeting_type"] in strategic_types:
        time_score = 100
    elif meeting["meeting_type"] in enablement_types:
        time_score = 75
    elif meeting["meeting_type"] in admin_types:
        time_score = 30
    else:
        time_score = 50
    
    final_score = int(type_score * 0.30 + okr_score * 0.35 + attendee_score * 0.20 + time_score * 0.15)
    
    if final_score >= 70:
        recommendation = "Keep"
    elif final_score >= 45:
        recommendation = "Delegate"
    else:
        recommendation = "Decline"
    
    return final_score, flags, recommendation, okr_relevance


def get_strategic_value_label(score):
    if score >= 75:
        return "High"
    elif score >= 50:
        return "Medium"
    return "Low"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            meetings = parse_calendar_csv()
            results = []
            
            for meeting in meetings:
                score, flags, recommendation, okr_relevance = calculate_alignment_score(meeting)
                result = {
                    "entry": meeting,
                    "alignment_score": score,
                    "strategic_value": get_strategic_value_label(score),
                    "flags": flags,
                    "recommendation": recommendation,
                    "okr_relevance": okr_relevance
                }
                results.append(result)
            
            results.sort(key=lambda x: x["alignment_score"])
            
            total = len(results)
            high_value = sum(1 for r in results if r["strategic_value"] == "High")
            needs_attention = sum(1 for r in results if r["recommendation"] != "Keep")
            
            response = {
                "summary": {
                    "total_meetings": total,
                    "high_strategic_value": high_value,
                    "needs_attention": needs_attention,
                    "health_score": int((high_value / total * 100) if total > 0 else 0)
                },
                "meetings": results
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
