from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class BusinessBase(BaseModel):
    name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    category: str
    location: str
    address: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    source: str = "google_maps"


class BusinessCreate(BusinessBase):
    pass


class Business(BusinessBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebsiteAnalysisBase(BaseModel):
    business_id: str
    screenshot_url: Optional[str] = None
    pagespeed_score: Optional[int] = None
    pagespeed_issues: Optional[dict] = None
    mobile_friendly: Optional[bool] = None
    ai_ui_score: Optional[float] = None
    ai_outdated: Optional[bool] = None
    ai_issues: Optional[list[str]] = None
    analysis_status: str = "pending"


class WebsiteAnalysisCreate(WebsiteAnalysisBase):
    pass


class WebsiteAnalysis(WebsiteAnalysisBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadBase(BaseModel):
    business_id: str
    lead_score: int
    priority: str = "low"
    outreach_message: Optional[str] = None
    redesign_suggestions: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class Lead(LeadBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadWithBusiness(Lead):
    business: Optional[Business] = None
    analysis: Optional[WebsiteAnalysis] = None


class PipelineRun(BaseModel):
    location: str
    category: str
    status: str = "running"
    businesses_found: int = 0
    businesses_analyzed: int = 0
    leads_generated: int = 0


class FetchBusinessesRequest(BaseModel):
    location: str
    category: str
    limit: int = Field(default=50, le=200)
    source: str = "mock"


class AnalyzeWebsiteRequest(BaseModel):
    business_id: str
    screenshot_only: bool = False


class RunPipelineRequest(BaseModel):
    location: str
    category: str
    limit: int = Field(default=50, le=200)


class LeadFilters(BaseModel):
    priority: Optional[str] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    has_website: Optional[bool] = None
    location: Optional[str] = None
    category: Optional[str] = None
    search: Optional[str] = None


class ExportRequest(BaseModel):
    format: str = "csv"
    filters: Optional[LeadFilters] = None


class PipelineRequestCreate(BaseModel):
    location: str
    category: str
    limit_count: int = 20


class DeleteLeadsByFilterRequest(BaseModel):
    priority: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
