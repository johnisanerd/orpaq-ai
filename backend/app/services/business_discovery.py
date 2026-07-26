import httpx
import asyncio
from typing import Optional
from app.config import settings

class BusinessDiscoveryService:
    def __init__(self):
        self.serpapi_key = settings.SERPAPI_KEY
        self.apify_key = settings.APIFY_API_KEY

    async def fetch_businesses(
        self, location: str, category: str, limit: int = 50, source: str = "apify"
    ) -> list[dict]:
        if source == "apify":
            if not self.apify_key:
                raise ValueError("APIFY_API_KEY is not configured")
            return await self._fetch_apify_businesses(location, category, limit)
        elif source == "serpapi":
            if not self.serpapi_key:
                raise ValueError("SERPAPI_KEY is not configured")
            return await self._fetch_serpapi_businesses(location, category, limit)
        
        raise ValueError(f"Invalid or unconfigured source: {source}")

    async def _fetch_apify_businesses(
        self, location: str, category: str, limit: int
    ) -> list[dict]:
        url = "https://api.apify.com/v2/acts/apify~google-maps-scraper/run-sync-get-dataset-items"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"location": location, "keyword": category, "maxResults": limit},
                headers={
                    "Authorization": f"Bearer {self.apify_key}",
                    "Content-Type": "application/json",
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return self._normalize_apify_data(data)
            else:
                raise Exception(f"Apify API error: {response.status_code} - {response.text}")

    async def _fetch_serpapi_businesses(
        self, location: str, category: str, limit: int
    ) -> list[dict]:
        url = "https://serpapi.com/search"

        params = {
            "q": f"{category} in {location}",
            "location": location,
            "num": limit,
            "api_key": self.serpapi_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                return self._normalize_serpapi_data(data)
            else:
                raise Exception(f"SerpAPI error: {response.status_code} - {response.text}")

    def _normalize_apify_data(self, data: list) -> list[dict]:
        normalized = []
        for item in data:
            normalized.append(
                {
                    "name": item.get("title", ""),
                    "website": item.get("website", None),
                    "phone": item.get("phone", None),
                    "email": item.get("email", None),
                    "category": item.get("type", ""),
                    "location": item.get("city", ""),
                    "address": item.get("address", None),
                    "rating": item.get("rating", None),
                    "reviews_count": item.get("reviewsCount", None),
                    "source": "apify",
                }
            )
        return normalized

    def _normalize_serpapi_data(self, data: dict) -> list[dict]:
        normalized = []
        for item in data.get("local_results", []):
            normalized.append(
                {
                    "name": item.get("title", ""),
                    "website": item.get("website", None),
                    "phone": item.get("phone", None),
                    "email": None,
                    "category": data.get("search_query", ""),
                    "location": data.get("location", ""),
                    "address": item.get("address", None),
                    "rating": item.get("rating", None),
                    "reviews_count": item.get("reviews", None),
                    "source": "serpapi",
                }
            )
        return normalized

business_discovery = BusinessDiscoveryService()
