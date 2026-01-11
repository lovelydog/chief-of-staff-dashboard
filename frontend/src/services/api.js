/**
 * API service for communicating with the FastAPI backend
 */

const API_BASE = 'http://localhost:8000/api';

/**
 * Fetch calendar audit results
 */
export async function getCalendarAudit() {
    const response = await fetch(`${API_BASE}/calendar-audit`);
    if (!response.ok) {
        throw new Error('Failed to fetch calendar audit');
    }
    return response.json();
}

/**
 * Fetch daily briefing for a specific date
 * @param {string} date - Date in YYYY-MM-DD format (optional, defaults to today)
 */
export async function getDailyBriefing(date = null) {
    const url = date
        ? `${API_BASE}/daily-briefing?date=${date}`
        : `${API_BASE}/daily-briefing`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('Failed to fetch daily briefing');
    }
    return response.json();
}

/**
 * Get available dates with calendar entries
 */
export async function getAvailableDates() {
    const response = await fetch(`${API_BASE}/available-dates`);
    if (!response.ok) {
        throw new Error('Failed to fetch available dates');
    }
    return response.json();
}

/**
 * Check text against communication style guidelines
 * @param {string} text - Text to analyze
 */
export async function checkStyle(text) {
    const response = await fetch(`${API_BASE}/check-style`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
    });
    if (!response.ok) {
        throw new Error('Failed to check style');
    }
    return response.json();
}

/**
 * Save feedback on a calendar audit decision
 * @param {number} meetingId - Meeting ID
 * @param {string} action - Action taken (keep, delegate, decline)
 * @param {string} notes - Optional notes
 */
export async function saveFeedback(meetingId, action, notes = null) {
    const response = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            meeting_id: meetingId,
            action,
            notes
        }),
    });
    if (!response.ok) {
        throw new Error('Failed to save feedback');
    }
    return response.json();
}

/**
 * Get all saved feedback
 */
export async function getFeedback() {
    const response = await fetch(`${API_BASE}/feedback`);
    if (!response.ok) {
        throw new Error('Failed to fetch feedback');
    }
    return response.json();
}
