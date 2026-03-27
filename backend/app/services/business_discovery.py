import httpx
import asyncio
from typing import Optional
from app.config import settings
import random


MOCK_BUSINESS_DATA = {
    "restaurants": [
        {
            "name": "La Bella Italia",
            "phone": "+1-555-0101",
            "category": "Italian Restaurant",
            "rating": 4.5,
        },
        {
            "name": "Sushi Master",
            "phone": "+1-555-0102",
            "category": "Japanese Restaurant",
            "rating": 4.8,
        },
        {
            "name": "Taco Loco",
            "phone": "+1-555-0103",
            "category": "Mexican Restaurant",
            "rating": 4.2,
        },
        {
            "name": "Golden Dragon",
            "phone": "+1-555-0104",
            "category": "Chinese Restaurant",
            "rating": 4.3,
        },
        {
            "name": "The Burger Joint",
            "phone": "+1-555-0105",
            "category": "American Restaurant",
            "rating": 4.1,
        },
    ],
    "clinics": [
        {
            "name": "City Medical Center",
            "phone": "+1-555-0201",
            "category": "Medical Clinic",
            "rating": 4.6,
        },
        {
            "name": "Smile Dental Care",
            "phone": "+1-555-0202",
            "category": "Dental Clinic",
            "rating": 4.7,
        },
        {
            "name": "Wellness Health Clinic",
            "phone": "+1-555-0203",
            "category": "General Clinic",
            "rating": 4.4,
        },
        {
            "name": "Family Practice Associates",
            "phone": "+1-555-0204",
            "category": "Family Medicine",
            "rating": 4.5,
        },
    ],
    "agencies": [
        {
            "name": "Creative Minds Agency",
            "phone": "+1-555-0301",
            "category": "Marketing Agency",
            "rating": 4.8,
        },
        {
            "name": "Tech Solutions Ltd",
            "phone": "+1-555-0302",
            "category": "IT Services",
            "rating": 4.6,
        },
        {
            "name": "Elite Real Estate",
            "phone": "+1-555-0303",
            "category": "Real Estate Agency",
            "rating": 4.4,
        },
        {
            "name": "Global Logistics Inc",
            "phone": "+1-555-0304",
            "category": "Logistics Agency",
            "rating": 4.3,
        },
    ],
    "salons": [
        {
            "name": "Glamour Hair Studio",
            "phone": "+1-555-0401",
            "category": "Hair Salon",
            "rating": 4.7,
        },
        {
            "name": "Zen Spa & Wellness",
            "phone": "+1-555-0402",
            "category": "Spa",
            "rating": 4.9,
        },
        {
            "name": "Nail Art Boutique",
            "phone": "+1-555-0403",
            "category": "Nail Salon",
            "rating": 4.5,
        },
        {
            "name": "Barber Bros",
            "phone": "+1-555-0404",
            "category": "Barbershop",
            "rating": 4.6,
        },
    ],
    "gyms": [
        {
            "name": "Iron Fitness Center",
            "phone": "+1-555-0501",
            "category": "Gym",
            "rating": 4.5,
        },
        {
            "name": "Yoga Bliss Studio",
            "phone": "+1-555-0502",
            "category": "Yoga Studio",
            "rating": 4.8,
        },
        {
            "name": "CrossFit Warriors",
            "phone": "+1-555-0503",
            "category": "CrossFit",
            "rating": 4.6,
        },
        {
            "name": "Planet Fitness",
            "phone": "+1-555-0504",
            "category": "Gym",
            "rating": 4.0,
        },
    ],
}


class BusinessDiscoveryService:
    def __init__(self):
        self.serpapi_key = settings.SERPAPI_KEY
        self.apify_key = settings.APIFY_API_KEY

    async def fetch_businesses(
        self, location: str, category: str, limit: int = 50, source: str = "mock"
    ) -> list[dict]:
        if source == "mock" or not self.apify_key:
            return await self._fetch_mock_businesses(location, category, limit)
        elif source == "apify":
            return await self._fetch_apify_businesses(location, category, limit)
        elif source == "serpapi":
            return await self._fetch_serpapi_businesses(location, category, limit)
        return []

    async def _fetch_mock_businesses(
        self, location: str, category: str, limit: int
    ) -> list[dict]:
        await asyncio.sleep(0.5)

        category_key = category.lower().replace(" ", "_").replace("-", "_")
        base_data = MOCK_BUSINESS_DATA.get(
            category_key, MOCK_BUSINESS_DATA["restaurants"]
        )

        businesses = []
        for i, base in enumerate(base_data[: min(limit, len(base_data))]):
            has_website = random.random() > 0.4
            website = (
                f"https://{base['name'].lower().replace(' ', '')}.com"
                if has_website
                else None
            )

            businesses.append(
                {
                    "name": base["name"],
                    "website": website,
                    "phone": base["phone"],
                    "email": f"contact@{base['name'].lower().replace(' ', '')}.com",
                    "category": base["category"],
                    "location": location,
                    "address": f"{random.randint(100, 999)} Main Street, {location}",
                    "rating": base["rating"],
                    "reviews_count": random.randint(10, 500),
                    "source": "google_maps",
                }
            )

        return businesses

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
            )

            if response.status_code == 200:
                data = response.json()
                return self._normalize_apify_data(data)

        return []

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
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                return self._normalize_serpapi_data(data)

        return []

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
