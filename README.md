# Orpaq AI

> **Zero-API-key lead generation platform** — Discovers businesses, analyzes websites, and scores leads using local tools. No external API keys required.

## What it does

1. **Discovers** businesses from Google Maps (name, phone, website)
2. **Analyzes** websites for quality (PageSpeed, mobile-friendliness)
3. **Scores** leads (HOT/Medium/Low) based on upgrade opportunity
4. **Outreach** — generates personalized messages for each lead
5. **Dashboard** — glassmorphic UI to view, filter, export leads

Everything runs locally. No API keys, no subscriptions.

## Quick start

```bash
# 1. Start the backend
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Start the frontend
cd frontend
npm run dev

# 3. Discover leads
python3 ~/.hermes/scripts/orpaq-research.py full "Kochi" "gyms" --max 20
```

Open http://localhost:3001 (frontend) or hit http://localhost:8000/api/v1 (API).

## Tech Stack

- **Backend**: FastAPI + SQLite
- **Frontend**: Next.js 16 + Tailwind CSS
- **Discovery**: Playwright (Google Maps scraping)
- **Analysis**: Playwright performance API
- **Scoring**: Local algorithm (no AI API needed)

## How it works

```
Google Maps (Playwright) → SQLite DB → FastAPI → Next.js Dashboard
         ↓
   Place page extraction (phone, website, rating)
         ↓
   Website analysis (PageSpeed, mobile check)
         ↓
   Lead scoring (HOT if no website)
```

## Data

- Database: `~/.orpaq/leads.db` (SQLite, auto-created)
- Suggestions auto-generated from your existing data
- No external API calls — everything runs on your machine

## Pipeline

```bash
# Full pipeline: discover + analyze + score
python3 ~/.hermes/scripts/orpaq-research.py full "Kochi" "dentists" --max 20

# Discover only (just scrape Maps)
python3 ~/.hermes/scripts/orpaq-research.py discover "Kochi" "gyms" --max 10

# Check what needs enrichment
python3 ~/.hermes/scripts/orpaq-research.py needs-enrich

# Save a lead manually
python3 ~/.hermes/scripts/orpaq-write.py lead '{"business_id":"<id>","lead_score":95,"priority":"hot"}'
```

## Environment

No API keys needed. The `.env` file is optional — defaults work out of the box.

| Variable | Default | Purpose |
|----------|---------|---------|
| `SQLITE_PATH` | `~/.orpaq/leads.db` | Database location |
