from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import (
    FetchBusinessesRequest,
    AnalyzeWebsiteRequest,
    RunPipelineRequest,
    LeadFilters,
    LeadWithBusiness,
    ExportRequest,
)
from app.services.database import db
from app.services.business_discovery import business_discovery
from app.services.pipeline import pipeline_service
import csv
import io
import json


router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orpaq-ai"}


@router.post("/fetch-businesses")
async def fetch_businesses(request: FetchBusinessesRequest):
    businesses = await business_discovery.fetch_businesses(
        location=request.location,
        category=request.category,
        limit=request.limit,
        source=request.source,
    )

    stored = []
    for business in businesses:
        stored_business = db.create_business(business)
        stored.append(stored_business)

    return {
        "location": request.location,
        "category": request.category,
        "found": len(businesses),
        "stored": len(stored),
        "businesses": stored[:10],
    }


@router.post("/analyze-website")
async def analyze_website(request: AnalyzeWebsiteRequest):
    business = db.get_business(request.business_id)

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business.get("website"):
        raise HTTPException(status_code=400, detail="No website to analyze")

    result = await pipeline_service.analyze_single_website(request.business_id)

    return result


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

    # Simple count for analyses
    try:
        if db.client:
            analyses = db.client.table("analyses").select("id", count="exact").execute()
            analyses_count = analyses.count if analyses else 0
        else:
            analyses_count = len(db._in_memory.get("analyses", []))
    except:
        analyses_count = 0

    return {
        "leads": stats,
        "total_businesses": len(businesses),
        "total_analyses": analyses_count,
    }


@router.post("/run-pipeline")
async def run_pipeline(request: RunPipelineRequest):
    result = await pipeline_service.run_full_pipeline(
        location=request.location, category=request.category, limit=request.limit
    )

    return result


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
