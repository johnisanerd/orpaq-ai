from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import (
    FetchBusinessesRequest,
    AnalyzeWebsiteRequest,
    RunPipelineRequest,
    LeadFilters,
    LeadWithBusiness,
    ExportRequest,
    PipelineRequestCreate,
    DeleteLeadsByFilterRequest,
)
from app.services.database import db
import csv
import io
import json
import sys
import subprocess
import threading
import uuid
import httpx
from pathlib import Path

RESEARCH_SCRIPT = str(Path.home() / ".hermes" / "scripts" / "orpaq-research.py")

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orpaq-ai"}


@router.post("/fetch-businesses")
async def fetch_businesses(request: FetchBusinessesRequest):
    """
    Discover businesses via the research engine (Playwright-based Google Maps scraping).
    Falls back to web_search if Maps scraping fails.
    """
    # Run the research engine's discover subcommand
    limit = request.limit or 20
    try:
        result = subprocess.run(
            [sys.executable or "python3", RESEARCH_SCRIPT, "discover",
             request.location, request.category, "--max", str(limit)],
            capture_output=True, text=True, timeout=120,
        )
        # Check DB for results
        recent_runs = db.get_pipeline_runs(limit=1)
        run_info = recent_runs[0] if recent_runs else {}
        stored_biz = db.get_businesses(location=request.location, category=request.category)
        return {
            "location": request.location,
            "category": request.category,
            "found": run_info.get("businesses_found", len(stored_biz)),
            "stored": len(stored_biz),
            "businesses": stored_biz[:10],
            "run_id": run_info.get("id"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-website")
async def analyze_website(request: AnalyzeWebsiteRequest):
    """
    Analyze a single business's website using the research engine.
    """
    business = db.get_business(request.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not business.get("website"):
        raise HTTPException(status_code=400, detail="No website to analyze")

    # Use the research engine to analyze
    try:
        # Run the analysis engine on this specific business
        result = subprocess.run(
            [sys.executable or "python3", RESEARCH_SCRIPT, "analyze",
             business.get("location", ""), business.get("category", ""), "--max", "10"],
            capture_output=True, text=True, timeout=120,
        )
        # Return the stored analysis from DB
        analysis = db.get_analysis(request.business_id)
        if not analysis:
            return {
                "business_id": request.business_id,
                "analysis_status": "error",
                "message": "Analysis did not produce results",
            }
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads")
async def get_leads(
    priority: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    has_website: Optional[bool] = Query(None),
    location: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
):
    filters = {}
    if priority:
        filters["priority"] = priority
    if min_score is not None:
        filters["min_score"] = min_score
    if max_score is not None:
        filters["max_score"] = max_score

    leads = db.get_leads(filters=filters, limit=limit)

    if location or category or search or has_website is not None:
        filtered = []
        for lead in leads:
            business = lead.get("businesses", {})
            if (
                location
                and location.lower() not in business.get("location", "").lower()
            ):
                continue
            if category and category.lower() != business.get("category", "").lower():
                continue
            if search and search.lower() not in business.get("name", "").lower():
                continue
            if has_website is not None:
                has_site = bool(business.get("website"))
                if has_site != has_website:
                    continue
            filtered.append(lead)
        leads = filtered

    return {"total": len(leads), "leads": leads}


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    lead = db.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/stats")
async def get_stats():
    stats = db.get_lead_stats()
    businesses = db.get_businesses(limit=1000)

    # Count analyses from SQLite
    try:
        cur = db.conn.execute("SELECT COUNT(*) as c FROM analyses")
        analyses_count = cur.fetchone()["c"]
    except:
        analyses_count = 0

    return {
        "leads": stats,
        "total_businesses": len(businesses),
        "total_analyses": analyses_count,
    }


@router.post("/run-pipeline")
async def run_pipeline(request: RunPipelineRequest):
    """
    Run the full lead research pipeline via the Hermes research engine.
    Launches in background thread; create a pipeline_run record immediately.
    """
    run_id = str(uuid.uuid4())
    now_str = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    # Create pipeline run record
    try:
        db.conn.execute(
            "INSERT INTO pipeline_runs (id, location, category, status, started_at) VALUES (?,?,?,?,?)",
            (run_id, request.location, request.category, "running", now_str),
        )
        db.conn.commit()
    except:
        pass

    def run_in_background():
        try:
            import sys as _sys
            result = subprocess.run(
                [_sys.executable or "python3", RESEARCH_SCRIPT, "full",
                 request.location, request.category, "--max", str(request.limit or 20),
                 "--run-id", run_id],
                capture_output=True, text=True, timeout=300,
            )
            # Update pipeline run status
            db.conn.execute(
                "UPDATE pipeline_runs SET status=?, completed_at=? WHERE id=?",
                ("completed", __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), run_id),
            )
            db.conn.commit()
        except Exception as e:
            try:
                db.conn.execute(
                    "UPDATE pipeline_runs SET status=?, errors=?, completed_at=? WHERE id=?",
                    ("failed", str(e)[:500], __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), run_id),
                )
                db.conn.commit()
            except:
                pass

    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()

    return {
        "run_id": run_id,
        "status": "running",
        "location": request.location,
        "category": request.category,
        "message": "Pipeline started. Refresh the dashboard to see results.",
    }


@router.post("/export")
async def export_leads(request: ExportRequest):
    filters = {}
    if request.filters:
        if request.filters.priority:
            filters["priority"] = request.filters.priority
        if request.filters.min_score:
            filters["min_score"] = request.filters.min_score
        if request.filters.max_score:
            filters["max_score"] = request.filters.max_score

    leads = db.get_leads(filters=filters, limit=1000)

    if request.filters:
        filtered = []
        for lead in leads:
            business = lead.get("businesses", {})
            if (
                request.filters.location
                and request.filters.location.lower()
                not in business.get("location", "").lower()
            ):
                continue
            if (
                request.filters.category
                and request.filters.category.lower()
                != business.get("category", "").lower()
            ):
                continue
            if (
                request.filters.search
                and request.filters.search.lower()
                not in business.get("name", "").lower()
            ):
                continue
            filtered.append(lead)
        leads = filtered

    if request.format == "json":
        return {"leads": leads}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Business Name",
            "Website",
            "Phone",
            "Category",
            "Location",
            "Lead Score",
            "Priority",
            "PageSpeed Score",
            "AI UI Score",
            "Outdated",
        ]
    )

    for lead in leads:
        business = lead.get("businesses", {})
        analysis = lead.get("analyses", {})
        writer.writerow(
            [
                business.get("name", ""),
                business.get("website", ""),
                business.get("phone", ""),
                business.get("category", ""),
                business.get("location", ""),
                lead.get("lead_score", ""),
                lead.get("priority", ""),
                analysis.get("pagespeed_score", ""),
                analysis.get("ai_ui_score", ""),
                "Yes" if analysis.get("ai_outdated") else "No",
            ]
        )

    return {"format": "csv", "data": output.getvalue()}


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    success = db.delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted successfully"}


@router.delete("/leads")
async def delete_leads_by_filter(request: DeleteLeadsByFilterRequest):
    """Delete all leads matching the given filters."""
    leads = db.get_leads(
        filters={
            "priority": request.priority,
            "location": request.location,
            "category": request.category,
        },
        limit=10000,
    )
    count = 0
    for lead in leads:
        if db.delete_lead(lead["id"]):
            count += 1
    return {"message": f"Deleted {count} leads"}


@router.post("/pipeline-requests")
async def create_pipeline_request(request: PipelineRequestCreate):
    req = db.create_pipeline_request(request.location, request.category, request.limit_count)
    return req


@router.get("/pipeline-requests")
async def list_pipeline_requests(limit: int = 20):
    cur = db.conn.execute("SELECT * FROM pipeline_requests ORDER BY requested_at DESC LIMIT ?", (limit,))
    all_requests = [dict(r) for r in cur.fetchall()]
    return all_requests


@router.get("/pipeline-runs")
async def list_pipeline_runs(limit: int = 20):
    return db.get_pipeline_runs(limit)


@router.get("/suggestions")
async def get_suggestions(location: Optional[str] = Query(None), limit: int = 12):
    """
    Auto-generate lead suggestions from existing data + known categories.
    """
    known_categories = [
        {"category": "dentists", "label": "Dentists", "desc": "Need booking + credibility sites", "priority": "high"},
        {"category": "salons", "label": "Salons", "desc": "Image-heavy, portfolio matters", "priority": "high"},
        {"category": "interior-designers", "label": "Interior Designers", "desc": "Portfolio = entire sales tool", "priority": "high"},
        {"category": "gyms", "label": "Gyms", "desc": "Schedule + pricing, many on IG only", "priority": "high"},
        {"category": "real-estate", "label": "Real Estate", "desc": "Listings portals, big projects", "priority": "high"},
        {"category": "clinics", "label": "Clinics", "desc": "Booking + credibility, high budget", "priority": "high"},
        {"category": "wedding-planners", "label": "Wedding Planners", "desc": "Portfolio + inquiry funnel", "priority": "medium"},
        {"category": "architects", "label": "Architects", "desc": "Portfolio is their resume", "priority": "medium"},
        {"category": "furniture", "label": "Furniture Stores", "desc": "E-commerce / catalog sites", "priority": "medium"},
        {"category": "event-management", "label": "Event Management", "desc": "Portfolio + booking system", "priority": "medium"},
        {"category": "restaurants", "label": "Restaurants", "desc": "Menu + location, quick turnarounds", "priority": "low"},
        {"category": "agencies", "label": "Agencies", "desc": "Should know better but often don't", "priority": "low"},
    ]

    # Get existing data from DB
    existing = {}
    try:
        rows = db.conn.execute(
            "SELECT category, location, COUNT(*) as cnt FROM businesses GROUP BY category, location ORDER BY cnt DESC LIMIT 50"
        ).fetchall()
        for row in rows:
            key = f"{row['category']}|{row['location']}"
            existing[key] = {"category": row["category"], "location": row["location"], "count": row["cnt"]}
    except:
        pass

    # Get lead counts per category-location
    lead_counts = {}
    try:
        rows = db.conn.execute(
            """SELECT b.category, b.location, COUNT(*) as cnt
               FROM leads l JOIN businesses b ON l.business_id = b.id
               GROUP BY b.category, b.location ORDER BY cnt DESC LIMIT 50"""
        ).fetchall()
        for row in rows:
            key = f"{row['category']}|{row['location']}"
            lead_counts[key] = row["cnt"]
    except:
        pass

    suggestions = []
    seen_keys = set()

    # 1. From existing businesses (you found businesses here before)
    for key, data in existing.items():
        cat = data["category"]
        loc = data["location"]
        if location and location.lower() not in loc.lower():
            continue
        k = f"{cat}|{loc}"
        seen_keys.add(k)

        match = next((c for c in known_categories if c["category"] == cat), None)
        suggestions.append({
            "category": cat,
            "location": loc,
            "label": match["label"] if match else cat.title(),
            "desc": f"Found {data['count']} businesses" + (f", {lead_counts.get(k, 0)} leads" if lead_counts.get(k) else ""),
            "priority": match["priority"] if match else "medium",
            "source": "existing",
            "count": data["count"],
            "lead_count": lead_counts.get(k, 0),
        })

    # 2. Fill in recommended categories with best-guess locations
    target_locations = ["Kochi", "Trivandrum", "Kozhikode", "Thrissur", "Palakkad"]
    for cat_info in known_categories:
        if len(suggestions) >= limit + 5:
            break
        cat = cat_info["category"]

        # For each known category, suggest locations that aren't already covered
        for target_loc in target_locations:
            if location and location.lower() not in target_loc.lower():
                continue
            k = f"{cat}|{target_loc}"
            if k in seen_keys:
                continue
            if len(suggestions) >= limit + 5:
                break
            seen_keys.add(k)
            suggestions.append({
                "category": cat,
                "location": target_loc,
                "label": cat_info["label"],
                "desc": cat_info["desc"],
                "priority": cat_info["priority"],
                "source": "recommended",
                "count": 0,
                "lead_count": 0,
            })

    # Sort: existing leads first, then by priority, then by count
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: (
        0 if s["source"] == "existing" and s["lead_count"] > 0 else
        1 if s["source"] == "existing" else 2,
        priority_order.get(s["priority"], 3),
        -s.get("lead_count", 0),
    ))

    return suggestions[:limit]

@router.post("/leads/{lead_id}/enrich")
async def enrich_lead(lead_id: str):
    """Re-trigger single-lead visual enrichment."""
    try:
        subprocess.run(
            ["hermes", "run", "-s", "orpaq-browser-search", "-c", f"enrich {lead_id}"],
            capture_output=True, text=True, timeout=300,
        )
        lead = db.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/whatsapp")
async def send_whatsapp(lead_id: str):
    """Wire lead outreach messages directly to the local WhatsApp browser bridge."""
    lead = db.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    phone = lead.get("businesses", {}).get("phone") or lead.get("business", {}).get("phone")
    message = lead.get("outreach_message")
    if not phone or not message:
        raise HTTPException(status_code=400, detail="Missing phone or message")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://127.0.0.1:10086/send", json={"phone": phone, "message": message}, timeout=30)
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="WhatsApp bridge failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "sent"}

