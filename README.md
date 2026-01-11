# Chief of Staff Dashboard 🎯

A personalized executive productivity dashboard that analyzes calendar alignment with OKRs, provides strategic meeting insights, and ensures communication consistency.

## Features

### 📊 Daily Briefing
- Timeline view of daily schedule with strategic value badges
- Stats showing total meetings, hours, and % strategic time
- Color-coded indicators for meeting value

### 🔍 Ruthless Calendar Audit
- Analyzes meetings against your OKRs and priorities
- Flags misaligned meetings (e.g., "CTO attending junior design review")
- Provides actionable recommendations: Keep, Delegate, or Decline

### ✍️ Drafting Assistant
- Checks text against your communication style guide
- Detects issues like passive voice, vague terms, missing metrics
- Flags pet peeves and over-apologizing

## Tech Stack

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python FastAPI
- **Storage**: File-based JSON

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Access the dashboard at http://localhost:5173

## Customization

Edit these files to personalize the dashboard:
- `user_profile.md` - Your role, OKRs, and meeting priorities
- `communication_style.md` - Your writing preferences and templates
- `calendar_sample.csv` - Your calendar data

## Screenshots

The dashboard features a professional dark theme with blue accents and includes:
- Summary cards with key metrics
- Expandable meeting details
- Real-time style analysis

## License

MIT
