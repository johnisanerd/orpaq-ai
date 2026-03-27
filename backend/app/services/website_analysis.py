import asyncio
import base64
import os
from pathlib import Path
from typing import Optional
import httpx
from playwright.async_api import async_playwright, Browser, Page
from app.config import settings


class WebsiteAnalysisService:
    def __init__(self):
        self.playwright: Optional[async_playwright] = None
        self.browser: Optional[Browser] = None
        self.screenshot_dir = Path("/tmp/orpaq-ai/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def init_browser(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def analyze_website(
        self, business_id: str, website_url: str, screenshot_only: bool = False
    ) -> dict:
        await self.init_browser()

        result = {
            "business_id": business_id,
            "screenshot_url": None,
            "screenshot_base64": None,
            "pagespeed_score": None,
            "pagespeed_issues": None,
            "mobile_friendly": None,
            "ai_ui_score": None,
            "ai_outdated": None,
            "ai_issues": None,
            "analysis_status": "completed",
        }

        try:
            screenshot_path = await self._capture_screenshot(business_id, website_url)
            if screenshot_path:
                result["screenshot_url"] = str(screenshot_path)
                with open(screenshot_path, "rb") as f:
                    result["screenshot_base64"] = base64.b64encode(f.read()).decode()

            if not screenshot_only:
                pagespeed = await self._run_pagespeed(website_url)
                if pagespeed:
                    result["pagespeed_score"] = pagespeed.get("score")
                    result["pagespeed_issues"] = pagespeed.get("issues")
                    result["mobile_friendly"] = pagespeed.get("mobile_friendly")

        except Exception as e:
            result["analysis_status"] = f"error: {str(e)}"

        return result

    async def _capture_screenshot(self, business_id: str, url: str) -> Optional[Path]:
        if not self.browser:
            await self.init_browser()

        page = await self.browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")

            await page.set_viewport_size({"width": 1920, "height": 1080})
            screenshot_path = self.screenshot_dir / f"{business_id}_desktop.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            await page.set_viewport_size({"width": 375, "height": 812})
            mobile_path = self.screenshot_dir / f"{business_id}_mobile.png"
            await page.screenshot(path=str(mobile_path), full_page=True)

            return screenshot_path

        except Exception as e:
            print(f"Screenshot error for {url}: {e}")
            return None
        finally:
            await page.close()

    async def _run_pagespeed(self, url: str) -> Optional[dict]:
        if not settings.PAGESPEED_API_KEY:
            return {
                "score": 75,
                "issues": ["Mock PageSpeed - API key not configured"],
                "mobile_friendly": True,
            }

        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

        params = {"url": url, "key": settings.PAGESPEED_API_KEY, "strategy": "mobile"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url, params=params, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    lighthouse = data.get("lighthouseResult", {})

                    categories = lighthouse.get("categories", {})
                    performance = categories.get("Performance", {})
                    score = (
                        int(performance.get("score", 0) * 100) if performance else None
                    )

                    audits = lighthouse.get("audits", {})
                    mobile_friendly = (
                        audits.get("viewport", {})
                        .get("score", {})
                        .get("numericValue", 1)
                        == 1
                    )

                    issues = []
                    for audit_id in [
                        "bootup-time",
                        "first-contentful-paint",
                        "largest-contentful-paint",
                    ]:
                        if audit_id in audits:
                            audit = audits[audit_id]
                            if audit.get("score", 1) < 0.5:
                                issues.append(audit.get("title", audit_id))

                    return {
                        "score": score,
                        "issues": issues[:5],
                        "mobile_friendly": mobile_friendly,
                    }
            except Exception as e:
                print(f"PageSpeed error: {e}")

        return None

    async def analyze_screenshot_with_ai(self, screenshot_base64: str) -> dict:
        if not settings.GROQ_API_KEY and not settings.OPENAI_API_KEY:
            return {
                "ui_score": 7.5,
                "outdated": False,
                "issues": ["Mock AI Analysis - API key not configured"],
                "suggestions": "Modern design with good contrast. Consider adding more white space.",
            }

        prompt = """Analyze this website screenshot and provide:
1. UI/UX score (1-10)
2. Is the website outdated? (yes/no)
3. List of issues (design, layout, readability, conversion problems)
4. Brief redesign suggestions

Respond in JSON format:
{
  "ui_score": <1-10>,
  "outdated": <yes/no>,
  "issues": [<issue1>, <issue2>],
  "suggestions": "<brief suggestions>"
}"""

        try:
            if settings.GROQ_API_KEY:
                from groq import AsyncGroq

                client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                model = "llama-3.2-11b-vision-preview"
            else:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                model = "gpt-4o-mini"

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "content": "Analyze this website screenshot:",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_base64}"
                                },
                            },
                        ],
                    },
                ],
                max_tokens=500,
            )

            import json

            result = json.loads(response.choices[0].message.content)
            return {
                "ui_score": result.get("ui_score", 5),
                "outdated": result.get("outdated", "no") == "yes",
                "issues": result.get("issues", []),
                "suggestions": result.get("suggestions", ""),
            }

        except Exception as e:
            print(f"AI analysis error: {e}")
            return {
                "ui_score": 5,
                "outdated": False,
                "issues": [str(e)],
                "suggestions": "",
            }


website_analysis = WebsiteAnalysisService()
