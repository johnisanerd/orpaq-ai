# Orpaq AI - Lead Generation Platform

## Quick Start

### 1. Clone & Install

```bash
cd /home/zius/Projects/orpaq-ai
```

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy the example env file and fill in your API keys:

```bash
cp backend/.env.example backend/.env
```

**Required for full functionality:**
- `SUPABASE_URL` + `SUPABASE_KEY` - Database (see Setup Supabase below)
- `OPENAI_API_KEY` - AI vision analysis (get from platform.openai.com)
- `PAGESPEED_API_KEY` - Performance scoring (free, get from Google)

**Optional (for testing without real data):**
- Leave others blank - the app uses mock data

### 3. Set Up Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a project
2. Go to SQL Editor and run:

```sql
-- Businesses table
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    website TEXT,
    phone TEXT,
    email TEXT,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    address TEXT,
    rating FLOAT,
    reviews_count INTEGER,
    source TEXT DEFAULT 'google_maps',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Website analyses table
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    screenshot_url TEXT,
    pagespeed_score INTEGER,
    pagespeed_issues JSONB,
    mobile_friendly BOOLEAN,
    ai_ui_score FLOAT,
    ai_outdated BOOLEAN,
    ai_issues JSONB,
    analysis_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Leads table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    lead_score INTEGER NOT NULL,
    priority TEXT DEFAULT 'low',
    outreach_message TEXT,
    redesign_suggestions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (optional - for production)
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
```

3. Get your credentials from Settings → API:
   - URL: Project URL
   - `SUPABASE_KEY`: anon public key
   - `SUPABASE_SERVICE_KEY`: service_role key (for backend)

### 4. Run the Application

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:3000

### 5. Run a Pipeline

1. In the dashboard, enter a location (e.g., "New York")
2. Select a category (e.g., "restaurants")
3. Click "Start Pipeline"
4. Watch as businesses are discovered, analyzed, and scored!

---

## Docker Deployment

```bash
# Build and run
docker-compose up --build

# Or run just backend
cd backend
docker build -t orpaq-backend .
docker run -p 8000:8000 --env-file .env orpaq-backend
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/fetch-businesses` | POST | Discover businesses |
| `/api/v1/analyze-website` | POST | Analyze a website |
| `/api/v1/run-pipeline` | POST | Run full pipeline |
| `/api/v1/leads` | GET | Get leads (with filters) |
| `/api/v1/leads/{id}` | GET | Get single lead |
| `/api/v1/stats` | GET | Get lead statistics |
| `/api/v1/export` | POST | Export leads (CSV/JSON) |

---

## Project Structure

```
orpaq-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── services/       # Business logic
│   │   ├── models/         # Pydantic schemas
│   │   ├── config.py      # Settings
│   │   └── main.py        # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # UI components
│   │   └── lib/           # API client, utils
│   ├── package.json
│   └── tailwind.config.ts
├── docker-compose.yml
└── .env.example
```

---

## Features

- **Business Discovery**: Fetch businesses from Google Maps (mock/Apify/SerpAPI)
- **Website Analysis**: Screenshot capture, PageSpeed scoring, AI vision analysis
- **Lead Scoring**: Automatic scoring (0-100) based on website quality
- **Dashboard**: Filter, search, sort leads with export capability
- **Glassmorphism UI**: Modern dark theme with blur effects

---

## Troubleshooting

**Playwright not working:**
```bash
playwright install chromium
playwright install-deps
```

**Supabase connection error:**
- Check your URL and keys in `.env`
- Ensure table names match (businesses, analyses, leads)

**Frontend can't connect to backend:**
- Check NEXT_PUBLIC_API_URL in frontend/.env
- Ensure backend is running on port 8000