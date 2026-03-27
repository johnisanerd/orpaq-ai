import asyncio
from datetime import datetime
from typing import Optional
from app.services.database import db
from app.services.business_discovery import business_discovery
from app.services.website_analysis import website_analysis
from app.services.lead_scoring import lead_scoring


class PipelineService:
    def __init__(self):
        self.db = db
        self.discovery = business_discovery
        self.analysis = website_analysis
        self.scoring = lead_scoring

    async def run_full_pipeline(
        self, location: str, category: str, limit: int = 50
    ) -> dict:
        start_time = datetime.utcnow()

        result = {
            "status": "running",
            "location": location,
            "category": category,
            "start_time": start_time.isoformat(),
            "businesses_found": 0,
            "businesses_stored": 0,
            "websites_analyzed": 0,
            "leads_generated": 0,
            "errors": [],
        }

        try:
            businesses = await self.discovery.fetch_businesses(
                location=location, category=category, limit=limit, source="mock"
            )
            result["businesses_found"] = len(businesses)

            for business_data in businesses:
                try:
                    business = self.db.create_business(business_data)
                    result["businesses_stored"] += 1

                    analysis_result = {
                        "screenshot_base64": None,
                        "screenshot_url": None,
                    }
                    ai_result = None

                    if business_data.get("website"):
                        analysis_result = await self.analysis.analyze_website(
                            business_id=business["id"],
                            website_url=business_data["website"],
                            screenshot_only=False,
                        )

                        if analysis_result.get("screenshot_base64"):
                            ai_result = await self.analysis.analyze_screenshot_with_ai(
                                analysis_result["screenshot_base64"]
                            )
                            analysis_result["ai_ui_score"] = ai_result.get("ui_score")
                            analysis_result["ai_outdated"] = ai_result.get("outdated")
                            analysis_result["ai_issues"] = ai_result.get("issues")

                        self.db.create_analysis(
                            {
                                "business_id": business["id"],
                                "screenshot_url": analysis_result.get("screenshot_url"),
                                "pagespeed_score": analysis_result.get(
                                    "pagespeed_score"
                                ),
                                "pagespeed_issues": analysis_result.get(
                                    "pagespeed_issues"
                                ),
                                "mobile_friendly": analysis_result.get(
                                    "mobile_friendly"
                                ),
                                "ai_ui_score": analysis_result.get("ai_ui_score"),
                                "ai_outdated": analysis_result.get("ai_outdated"),
                                "ai_issues": analysis_result.get("ai_issues"),
                                "analysis_status": analysis_result.get(
                                    "analysis_status", "completed"
                                ),
                            }
                        )
                        result["websites_analyzed"] += 1

                        scoring = self.scoring.calculate_score(
                            has_website=True,
                            pagespeed_score=analysis_result.get("pagespeed_score"),
                            ai_ui_score=analysis_result.get("ai_ui_score"),
                            mobile_friendly=analysis_result.get("mobile_friendly"),
                        )
                    else:
                        scoring = self.scoring.calculate_score(has_website=False)

                    outreach = self.scoring.generate_outreach_message(
                        business_name=business_data["name"],
                        category=business_data["category"],
                        issues=analysis_result.get("ai_issues", [])
                        if business_data.get("website")
                        else ["No website found"],
                        suggestions=ai_result.get("suggestions", "")
                        if ai_result
                        else "",
                    )

                    lead = self.db.create_lead(
                        {
                            "business_id": business["id"],
                            "lead_score": scoring["score"],
                            "priority": scoring["priority"],
                            "outreach_message": outreach,
                            "redesign_suggestions": ai_result.get("suggestions", "")
                            if ai_result
                            else "Create a professional website",
                        }
                    )
                    result["leads_generated"] += 1

                except Exception as e:
                    result["errors"].append(
                        f"Error processing {business_data.get('name')}: {str(e)}"
                    )
                    continue

            result["status"] = "completed"
            result["end_time"] = datetime.utcnow().isoformat()

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))

        return result

    async def analyze_single_website(self, business_id: str) -> dict:
        business = self.db.get_business(business_id)
        if not business:
            return {"error": "Business not found"}

        if not business.get("website"):
            return {"error": "No website to analyze"}

        analysis_result = await self.analysis.analyze_website(
            business_id=business_id,
            website_url=business["website"],
            screenshot_only=False,
        )

        ai_result = None
        if analysis_result.get("screenshot_base64"):
            ai_result = await self.analysis.analyze_screenshot_with_ai(
                analysis_result["screenshot_base64"]
            )
            analysis_result["ai_ui_score"] = ai_result.get("ui_score")
            analysis_result["ai_outdated"] = ai_result.get("outdated")
            analysis_result["ai_issues"] = ai_result.get("issues")

        existing_analysis = self.db.get_analysis(business_id)
        if existing_analysis:
            self.db.update_analysis(existing_analysis["id"], analysis_result)
        else:
            self.db.create_analysis({**analysis_result, "business_id": business_id})

        scoring = self.scoring.calculate_score(
            has_website=True,
            pagespeed_score=analysis_result.get("pagespeed_score"),
            ai_ui_score=analysis_result.get("ai_ui_score"),
            mobile_friendly=analysis_result.get("mobile_friendly"),
        )

        existing_leads = self.db.get_leads(filters={"business_id": business_id})
        if existing_leads:
            self.db.update_lead(
                existing_leads[0]["id"],
                {"lead_score": scoring["score"], "priority": scoring["priority"]},
            )

        return {"business": business, "analysis": analysis_result, "scoring": scoring}


pipeline_service = PipelineService()
