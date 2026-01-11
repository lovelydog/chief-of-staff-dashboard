"""Pydantic models for API requests and responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import date, time


class CalendarEntry(BaseModel):
    """Represents a single calendar entry."""
    id: int
    title: str
    date: date
    start_time: time
    end_time: time
    duration_minutes: int
    organizer: str
    attendees: list[str]
    meeting_type: str
    description: str
    recurring: bool


class AuditResult(BaseModel):
    """Result of auditing a single calendar entry."""
    entry: CalendarEntry
    alignment_score: int  # 0-100
    strategic_value: str  # "High", "Medium", "Low"
    flags: list[str]  # List of concerns/warnings
    recommendation: str  # "Keep", "Delegate", "Decline"
    okr_relevance: list[str]  # Which OKRs this relates to


class DailyBriefing(BaseModel):
    """Daily briefing summary."""
    date: date
    total_meetings: int
    total_hours: float
    strategic_hours: float
    strategic_percentage: int
    meetings: list[AuditResult]


class StyleCheckRequest(BaseModel):
    """Request to check communication style."""
    text: str


class StyleIssue(BaseModel):
    """A single style issue found in text."""
    category: str
    issue: str
    suggestion: str
    severity: str  # "high", "medium", "low"


class StyleCheckResponse(BaseModel):
    """Response from communication style check."""
    score: int  # 0-100
    issues: list[StyleIssue]
    summary: str
    improved_version: Optional[str] = None


class FeedbackEntry(BaseModel):
    """User feedback on a calendar audit result."""
    meeting_id: int
    action: str  # "keep", "delegate", "decline"
    notes: Optional[str] = None
