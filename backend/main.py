"""Chief of Staff Dashboard - FastAPI Backend."""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.calendar_audit import audit_calendar, get_daily_briefing
from services.style_checker import check_communication_style

# Paths
BASE_DIR = Path(__file__).parent.parent
CALENDAR_CSV = BASE_DIR / "calendar_sample.csv"
FEEDBACK_FILE = Path(__file__).parent / "data" / "feedback.json"

# Initialize FastAPI app
app = FastAPI(
    title="Chief of Staff Dashboard API",
    description="Personal executive productivity dashboard backend",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class StyleCheckRequest(BaseModel):
    text: str


class FeedbackRequest(BaseModel):
    meeting_id: int
    action: str  # "keep", "delegate", "decline"
    notes: Optional[str] = None


# Health check
@app.get("/")
def root():
    return {"status": "healthy", "service": "Chief of Staff Dashboard API"}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# Calendar Audit endpoints
@app.get("/api/calendar-audit")
def get_calendar_audit():
    """
    Perform ruthless calendar audit.
    Analyzes all meetings against user's OKRs and priorities.
    Returns meetings sorted by alignment score (lowest first to highlight issues).
    """
    if not CALENDAR_CSV.exists():
        raise HTTPException(status_code=404, detail="Calendar CSV not found")
    
    try:
        results = audit_calendar(CALENDAR_CSV)
        
        # Convert dates and times to strings for JSON serialization
        for result in results:
            entry = result["entry"]
            entry["date"] = entry["date"].isoformat()
            entry["start_time"] = entry["start_time"].strftime("%H:%M")
            entry["end_time"] = entry["end_time"].strftime("%H:%M")
        
        # Summary stats
        total = len(results)
        high_value = sum(1 for r in results if r["strategic_value"] == "High")
        needs_attention = sum(1 for r in results if r["recommendation"] != "Keep")
        
        return {
            "summary": {
                "total_meetings": total,
                "high_strategic_value": high_value,
                "needs_attention": needs_attention,
                "health_score": int((high_value / total * 100) if total > 0 else 0)
            },
            "meetings": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/daily-briefing")
def get_daily_briefing_endpoint(date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")):
    """
    Get daily briefing for a specific date.
    Shows today's meetings with strategic value scores and prep notes.
    """
    if not CALENDAR_CSV.exists():
        raise HTTPException(status_code=404, detail="Calendar CSV not found")
    
    try:
        # Parse date or use today
        target_date = None
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        
        briefing = get_daily_briefing(CALENDAR_CSV, target_date)
        
        # Convert dates and times for JSON
        briefing["date"] = briefing["date"].isoformat()
        for meeting in briefing["meetings"]:
            entry = meeting["entry"]
            entry["date"] = entry["date"].isoformat()
            entry["start_time"] = entry["start_time"].strftime("%H:%M")
            entry["end_time"] = entry["end_time"].strftime("%H:%M")
        
        return briefing
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/available-dates")
def get_available_dates():
    """Get list of dates that have calendar entries."""
    if not CALENDAR_CSV.exists():
        raise HTTPException(status_code=404, detail="Calendar CSV not found")
    
    try:
        results = audit_calendar(CALENDAR_CSV)
        dates = sorted(set(r["entry"]["date"].isoformat() for r in results))
        return {"dates": dates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Style Checker endpoint
@app.post("/api/check-style")
def check_style(request: StyleCheckRequest):
    """
    Check text against communication style guidelines.
    Returns score, issues found, and suggestions for improvement.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    result = check_communication_style(request.text)
    return result


# Feedback endpoints
@app.post("/api/feedback")
def save_feedback(request: FeedbackRequest):
    """Save user feedback on a calendar audit decision."""
    try:
        # Load existing feedback
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {"feedback": []}
        
        # Add new feedback
        feedback_entry = {
            "meeting_id": request.meeting_id,
            "action": request.action,
            "notes": request.notes,
            "timestamp": datetime.now().isoformat()
        }
        data["feedback"].append(feedback_entry)
        
        # Save
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"status": "saved", "entry": feedback_entry}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feedback")
def get_feedback():
    """Get all saved feedback."""
    try:
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE, 'r') as f:
                return json.load(f)
        return {"feedback": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
