from typing import Optional


class LeadScoringService:
    def __init__(self):
        self.score_weights = {
            "no_website": 100,
            "low_pagespeed": 30,
            "low_ai_score": 40,
            "not_mobile_friendly": 30,
        }

    def calculate_score(
        self,
        has_website: bool,
        pagespeed_score: Optional[int] = None,
        ai_ui_score: Optional[float] = None,
        mobile_friendly: Optional[bool] = None,
    ) -> dict:
        score = 0
        factors = []

        if not has_website:
            score += self.score_weights["no_website"]
            factors.append(
                {
                    "factor": "no_website",
                    "points": self.score_weights["no_website"],
                    "reason": "No website - highest priority",
                }
            )

        if pagespeed_score is not None and pagespeed_score < 50:
            score += self.score_weights["low_pagespeed"]
            factors.append(
                {
                    "factor": "low_pagespeed",
                    "points": self.score_weights["low_pagespeed"],
                    "reason": f"Poor PageSpeed score: {pagespeed_score}",
                }
            )

        if ai_ui_score is not None and ai_ui_score < 5:
            score += self.score_weights["low_ai_score"]
            factors.append(
                {
                    "factor": "low_ai_score",
                    "points": self.score_weights["low_ai_score"],
                    "reason": f"Poor UI score: {ai_ui_score}/10",
                }
            )

        if mobile_friendly is not None and not mobile_friendly:
            score += self.score_weights["not_mobile_friendly"]
            factors.append(
                {
                    "factor": "not_mobile_friendly",
                    "points": self.score_weights["not_mobile_friendly"],
                    "reason": "Not mobile-friendly",
                }
            )

        priority = self._determine_priority(score)

        return {
            "score": score,
            "priority": priority,
            "factors": factors,
            "score_breakdown": self._get_score_breakdown(score),
        }

    def _determine_priority(self, score: int) -> str:
        if score >= 80:
            return "hot"
        elif score >= 50:
            return "medium"
        return "low"

    def _get_score_breakdown(self, score: int) -> dict:
        if score >= 80:
            return {
                "label": "HOT LEAD",
                "description": "High priority - immediate outreach recommended",
                "color": "red",
            }
        elif score >= 50:
            return {
                "label": "MEDIUM LEAD",
                "description": "Good potential - add to follow-up list",
                "color": "yellow",
            }
        return {
            "label": "LOW LEAD",
            "description": "Future opportunity - nurture over time",
            "color": "gray",
        }

    def generate_outreach_message(
        self,
        business_name: str,
        category: str,
        issues: list[str],
        suggestions: str,
        tone: str = "professional",
    ) -> str:
        if tone == "friendly":
            template = f"""Hi {business_name} team! 👋

I came across your {category} business and loved what I saw! 

I noticed a few opportunities to help you attract more customers online:
{self._format_issues(issues)}

Would you be interested in a quick chat about how we could help improve your online presence? We'd love to show you some ideas!

Best regards"""
        else:
            template = f"""Dear {business_name} Team,

I recently discovered your {category} business and I'm reaching out to offer some insights that could help you grow.

Our analysis identified a few areas for improvement:
{self._format_issues(issues)}

{self._format_suggestions(suggestions)}

We're offering a free consultation to discuss how we can help improve your digital presence.

Best regards"""

        return template

    def _format_issues(self, issues: list[str]) -> str:
        if not issues:
            return "- General website optimization opportunities"
        return "\n".join([f"- {issue}" for issue in issues[:3]])

    def _format_suggestions(self, suggestions: str) -> str:
        if not suggestions:
            return "We can provide recommendations tailored to your business goals."
        return suggestions[:200] + "..." if len(suggestions) > 200 else suggestions


lead_scoring = LeadScoringService()
