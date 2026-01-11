"""Calendar audit service - analyzes calendar against user's OKRs and priorities."""
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


# Keywords and patterns for OKR matching
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

# Meeting types and their base strategic value
MEETING_TYPE_SCORES = {
    "architecture": 95,
    "strategic_planning": 90,
    "board_prep": 90,
    "one_on_one": 85,
    "hiring": 80,
    "interview": 75,  # Depends on role level
    "incident_review": 85,
    "external": 70,
    "design_review": 60,  # Depends on seniority
    "sprint_ceremony": 30,
    "standup": 25,
    "status_update": 20,
    "vendor_demo": 40,  # Depends on deal size
    "adhoc": 35,
    "prep": 50,
    "strategic": 80,
}

# Keywords indicating junior-level activities
JUNIOR_INDICATORS = ["junior", "intern", "new hire", "onboarding", "coffee chat"]

# Keywords indicating senior-level activities
SENIOR_INDICATORS = ["staff", "principal", "director", "vp", "cto", "ceo", "cfo", "board", "investor"]


def parse_calendar_csv(csv_path: Path) -> list[dict]:
    """Parse calendar CSV file into list of meeting dictionaries."""
    meetings = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meeting = {
                "id": int(row["id"]),
                "title": row["title"],
                "date": datetime.strptime(row["date"], "%Y-%m-%d").date(),
                "start_time": datetime.strptime(row["start_time"], "%H:%M").time(),
                "end_time": datetime.strptime(row["end_time"], "%H:%M").time(),
                "duration_minutes": int(row["duration_minutes"]),
                "organizer": row["organizer"],
                "attendees": [a.strip() for a in row["attendees"].split(";")],
                "meeting_type": row["meeting_type"],
                "description": row["description"],
                "recurring": row["recurring"].lower() == "true"
            }
            meetings.append(meeting)
    return meetings


def find_okr_relevance(meeting: dict) -> list[str]:
    """Determine which OKRs a meeting is relevant to."""
    relevant_okrs = []
    text_to_search = f"{meeting['title']} {meeting['description']} {meeting['meeting_type']}".lower()
    
    if any(kw in text_to_search for kw in OKR_KEYWORDS["platform_modernization"]):
        relevant_okrs.append("Platform Modernization")
    if any(kw in text_to_search for kw in OKR_KEYWORDS["engineering_team"]):
        relevant_okrs.append("Build World-Class Engineering Team")
    if any(kw in text_to_search for kw in OKR_KEYWORDS["ai_ml_integration"]):
        relevant_okrs.append("AI/ML Integration")
    
    return relevant_okrs


def calculate_alignment_score(meeting: dict) -> tuple[int, list[str], str]:
    """
    Calculate alignment score for a meeting.
    Returns: (score, flags, recommendation)
    """
    flags = []
    score = 50  # Base score
    text_lower = f"{meeting['title']} {meeting['description']}".lower()
    attendees_lower = " ".join(meeting["attendees"]).lower()
    
    # Factor 1: Meeting Type (30% weight)
    base_type_score = MEETING_TYPE_SCORES.get(meeting["meeting_type"], 40)
    type_score = base_type_score
    
    # Factor 2: OKR Alignment (35% weight)
    okr_relevance = find_okr_relevance(meeting)
    if okr_relevance:
        okr_score = min(100, 70 + len(okr_relevance) * 15)
    else:
        okr_score = 30
        flags.append("No clear OKR alignment detected")
    
    # Factor 3: Attendee/Seniority Appropriateness (20% weight)
    attendee_score = 60  # Default
    is_junior_activity = any(ind in text_lower for ind in JUNIOR_INDICATORS)
    is_senior_activity = any(ind in text_lower or ind in attendees_lower for ind in SENIOR_INDICATORS)
    
    if is_junior_activity and not is_senior_activity:
        attendee_score = 25
        flags.append(f"CTO attending junior-level activity: '{meeting['title']}'")
    elif is_senior_activity:
        attendee_score = 90
    
    # Special case: Junior design reviews
    if meeting["meeting_type"] == "design_review" and is_junior_activity:
        type_score = 20
        flags.append("Design review should be delegated to Engineering Manager")
    
    # Special case: Junior interviews (CTO shouldn't do these)
    if meeting["meeting_type"] == "interview" and is_junior_activity:
        type_score = 25
        flags.append("Interview for junior role - delegate to hiring manager")
    
    # Special case: Small vendor demos
    if meeting["meeting_type"] == "vendor_demo":
        if "25k" in text_lower or "10k" in text_lower:
            type_score = 20
            flags.append("Vendor demo for tool under $50K threshold - delegate")
        elif "200k" in text_lower or "100k" in text_lower:
            type_score = 70  # Worth attending
    
    # Special case: Status updates should be async
    if meeting["meeting_type"] == "status_update":
        flags.append("Status updates should be asynchronous - consider declining")
        type_score = 15
    
    # Special case: Sprint ceremonies (CTO shouldn't attend unless critical)
    if meeting["meeting_type"] == "sprint_ceremony":
        flags.append("Sprint ceremony - CTO attendance rarely necessary")
    
    # Factor 4: Time Allocation Category (15% weight)
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
    
    # Calculate weighted final score
    final_score = int(
        type_score * 0.30 +
        okr_score * 0.35 +
        attendee_score * 0.20 +
        time_score * 0.15
    )
    
    # Determine recommendation
    if final_score >= 70:
        recommendation = "Keep"
    elif final_score >= 45:
        recommendation = "Delegate"
    else:
        recommendation = "Decline"
    
    return final_score, flags, recommendation


def get_strategic_value_label(score: int) -> str:
    """Convert numeric score to strategic value label."""
    if score >= 75:
        return "High"
    elif score >= 50:
        return "Medium"
    else:
        return "Low"


def audit_calendar(csv_path: Path) -> list[dict]:
    """
    Perform full calendar audit.
    Returns list of audit results.
    """
    meetings = parse_calendar_csv(csv_path)
    results = []
    
    for meeting in meetings:
        score, flags, recommendation = calculate_alignment_score(meeting)
        okr_relevance = find_okr_relevance(meeting)
        
        result = {
            "entry": meeting,
            "alignment_score": score,
            "strategic_value": get_strategic_value_label(score),
            "flags": flags,
            "recommendation": recommendation,
            "okr_relevance": okr_relevance
        }
        results.append(result)
    
    # Sort by score (lowest first to highlight problems)
    results.sort(key=lambda x: x["alignment_score"])
    
    return results


def get_daily_briefing(csv_path: Path, target_date: Optional[datetime] = None) -> dict:
    """
    Generate daily briefing for a specific date.
    """
    if target_date is None:
        target_date = datetime.now().date()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()
    
    all_results = audit_calendar(csv_path)
    
    # Filter for target date
    day_results = [
        r for r in all_results 
        if r["entry"]["date"] == target_date
    ]
    
    # Sort by start time for daily view
    day_results.sort(key=lambda x: x["entry"]["start_time"])
    
    # Calculate statistics
    total_minutes = sum(r["entry"]["duration_minutes"] for r in day_results)
    strategic_minutes = sum(
        r["entry"]["duration_minutes"] 
        for r in day_results 
        if r["strategic_value"] == "High"
    )
    
    total_hours = total_minutes / 60
    strategic_hours = strategic_minutes / 60
    strategic_pct = int((strategic_minutes / total_minutes * 100) if total_minutes > 0 else 0)
    
    return {
        "date": target_date,
        "total_meetings": len(day_results),
        "total_hours": round(total_hours, 1),
        "strategic_hours": round(strategic_hours, 1),
        "strategic_percentage": strategic_pct,
        "meetings": day_results
    }
