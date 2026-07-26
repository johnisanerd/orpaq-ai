from typing import Optional


class LeadScoringService:
    def __init__(self):
        self.score_weights = {
            # No website = highest opportunity
            "no_website": 95,
            # Poor website = high opportunity for redesign
            "very_slow_pagespeed": 25,
            "slow_pagespeed": 15,
            "low_ai_score": 20,
            "medium_ai_score": 10,
            "not_mobile_friendly": 20,
            "outdated_design": 15,
            # Low rating = needs marketing help
            "low_rating": 10,
            # High rating but bad site = missed opportunity
            "high_rating_no_site": 15,
        }

    def calculate_score(
        self,
        has_website: bool,
        pagespeed_score: Optional[int] = None,
        ai_ui_score: Optional[float] = None,
        mobile_friendly: Optional[bool] = None,
        rating: Optional[float] = None,
        outdated: Optional[bool] = None,
    ) -> dict:
        score = 0
        factors = []

        if not has_website:
            score += self.score_weights["no_website"]
            factors.append(
                {
                    "factor": "no_website",
                    "points": self.score_weights["no_website"],
                    "reason": "No website - highest opportunity for new business",
                }
            )
            # Bonus if business has good rating but no website
            if rating and rating >= 4.5:
                score += self.score_weights["high_rating_no_site"]
                factors.append(
                    {
                        "factor": "high_rating_no_site",
                        "points": self.score_weights["high_rating_no_site"],
                        "reason": f"High rating ({rating}) but no website - proven quality, huge missed opportunity",
                    }
                )
        else:
            # Pagespeed scoring
            if pagespeed_score is not None:
                if pagespeed_score < 30:
                    score += self.score_weights["very_slow_pagespeed"]
                    factors.append(
                        {
                            "factor": "very_slow_pagespeed",
                            "points": self.score_weights["very_slow_pagespeed"],
                            "reason": f"Very slow PageSpeed: {pagespeed_score}/100 - losing customers",
                        }
                    )
                elif pagespeed_score < 50:
                    score += self.score_weights["slow_pagespeed"]
                    factors.append(
                        {
                            "factor": "slow_pagespeed",
                            "points": self.score_weights["slow_pagespeed"],
                            "reason": f"Slow PageSpeed: {pagespeed_score}/100 - needs optimization",
                        }
                    )

            # UI score scoring
            if ai_ui_score is not None:
                if ai_ui_score < 4:
                    score += self.score_weights["low_ai_score"]
                    factors.append(
                        {
                            "factor": "low_ai_score",
                            "points": self.score_weights["low_ai_score"],
                            "reason": f"Poor UI/UX score: {ai_ui_score:.1f}/10 - needs redesign",
                        }
                    )
                elif ai_ui_score < 6:
                    score += self.score_weights["medium_ai_score"]
                    factors.append(
                        {
                            "factor": "medium_ai_score",
                            "points": self.score_weights["medium_ai_score"],
                            "reason": f"Average UI/UX score: {ai_ui_score:.1f}/10 - room for improvement",
                        }
                    )

            # Mobile friendly
            if mobile_friendly is not None and not mobile_friendly:
                score += self.score_weights["not_mobile_friendly"]
                factors.append(
                    {
                        "factor": "not_mobile_friendly",
                        "points": self.score_weights["not_mobile_friendly"],
                        "reason": "Not mobile-friendly - losing 60% of mobile traffic",
                    }
                )

            # Outdated design
            if outdated:
                score += self.score_weights["outdated_design"]
                factors.append(
                    {
                        "factor": "outdated_design",
                        "points": self.score_weights["outdated_design"],
                        "reason": "Outdated design - customers prefer modern competitors",
                    }
                )

        # Low rating bonus (business needs marketing help)
        if rating and rating < 3.5:
            score += self.score_weights["low_rating"]
            factors.append(
                {
                    "factor": "low_rating",
                    "points": self.score_weights["low_rating"],
                    "reason": f"Low rating ({rating}) - reputation management needed",
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
