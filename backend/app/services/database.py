from supabase import create_client, Client
from typing import Optional, Any
from datetime import datetime
import uuid

from app.config import settings


class Database:
    client: Optional[Client] = None
    _in_memory: dict = {"businesses": [], "analyses": [], "leads": []}

    def init(self):
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                self.client = create_client(
                    settings.SUPABASE_URL, settings.SUPABASE_KEY
                )
            except Exception as e:
                print(f"Supabase connection failed: {e}")

    def create_business(self, data: dict) -> dict:
        if not self.client:
            record = {
                "id": str(uuid.uuid4()),
                **data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._in_memory["businesses"].append(record)
            return record

        data["id"] = str(uuid.uuid4())
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()
        response = self.client.table("businesses").insert(data).execute()
        return response.data[0] if response.data else data

    def get_business(self, business_id: str) -> Optional[dict]:
        if not self.client:
            for b in self._in_memory["businesses"]:
                if b["id"] == business_id:
                    return b
            return None
        response = (
            self.client.table("businesses").select("*").eq("id", business_id).execute()
        )
        return response.data[0] if response.data else None

    def get_businesses(
        self,
        location: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        if not self.client:
            results = self._in_memory["businesses"]
            if location:
                results = [
                    b
                    for b in results
                    if location.lower() in b.get("location", "").lower()
                ]
            if category:
                results = [
                    b
                    for b in results
                    if category.lower() in b.get("category", "").lower()
                ]
            return results[:limit]

        query = self.client.table("businesses").select("*")
        if location:
            query = query.ilike("location", f"%{location}%")
        if category:
            query = query.eq("category", category)
        response = query.limit(limit).execute()
        return response.data or []

    def update_business(self, business_id: str, data: dict) -> dict:
        if not self.client:
            for i, b in enumerate(self._in_memory["businesses"]):
                if b["id"] == business_id:
                    b.update(data)
                    b["updated_at"] = datetime.utcnow().isoformat()
                    return b
            return {"id": business_id, **data}
        data["updated_at"] = datetime.utcnow().isoformat()
        response = (
            self.client.table("businesses").update(data).eq("id", business_id).execute()
        )
        return response.data[0] if response.data else data

    def create_analysis(self, data: dict) -> dict:
        if not self.client:
            record = {
                "id": str(uuid.uuid4()),
                **data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._in_memory["analyses"].append(record)
            return record

        data["id"] = str(uuid.uuid4())
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()
        response = self.client.table("analyses").insert(data).execute()
        return response.data[0] if response.data else data

    def get_analysis(self, business_id: str) -> Optional[dict]:
        if not self.client:
            for a in self._in_memory["analyses"]:
                if a.get("business_id") == business_id:
                    return a
            return None
        response = (
            self.client.table("analyses")
            .select("*")
            .eq("business_id", business_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def update_analysis(self, analysis_id: str, data: dict) -> dict:
        if not self.client:
            for i, a in enumerate(self._in_memory["analyses"]):
                if a["id"] == analysis_id:
                    a.update(data)
                    a["updated_at"] = datetime.utcnow().isoformat()
                    return a
            return {"id": analysis_id, **data}
        data["updated_at"] = datetime.utcnow().isoformat()
        response = (
            self.client.table("analyses").update(data).eq("id", analysis_id).execute()
        )
        return response.data[0] if response.data else data

    def create_lead(self, data: dict) -> dict:
        if not self.client:
            record = {
                "id": str(uuid.uuid4()),
                **data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._in_memory["leads"].append(record)
            return record

        data["id"] = str(uuid.uuid4())
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()
        response = self.client.table("leads").insert(data).execute()
        return response.data[0] if response.data else data

    def get_leads(self, filters: Optional[dict] = None, limit: int = 100) -> list[dict]:
        if not self.client:
            leads = self._in_memory["leads"]
            if filters:
                if "priority" in filters and filters["priority"]:
                    leads = [
                        l for l in leads if l.get("priority") == filters["priority"]
                    ]
                if "min_score" in filters and filters["min_score"]:
                    leads = [
                        l
                        for l in leads
                        if l.get("lead_score", 0) >= filters["min_score"]
                    ]
                if "max_score" in filters and filters["max_score"]:
                    leads = [
                        l
                        for l in leads
                        if l.get("lead_score", 0) <= filters["max_score"]
                    ]
            results = sorted(leads, key=lambda x: x.get("lead_score", 0), reverse=True)[
                :limit
            ]
            enriched = []
            for lead in results:
                business = next(
                    (
                        b
                        for b in self._in_memory["businesses"]
                        if b["id"] == lead.get("business_id")
                    ),
                    None,
                )
                analysis = next(
                    (
                        a
                        for a in self._in_memory["analyses"]
                        if a.get("business_id") == lead.get("business_id")
                    ),
                    None,
                )
                enriched.append(
                    {**lead, "businesses": business or {}, "analyses": analysis or {}}
                )
            return enriched

        # Get leads
        query = self.client.table("leads").select("*")
        if filters:
            if "priority" in filters and filters["priority"]:
                query = query.eq("priority", filters["priority"])
            if "min_score" in filters and filters["min_score"]:
                query = query.gte("lead_score", filters["min_score"])
            if "max_score" in filters and filters["max_score"]:
                query = query.lte("lead_score", filters["max_score"])
        leads_data = (
            query.order("lead_score", desc=True).limit(limit).execute().data or []
        )

        # Get related businesses and analyses separately
        enriched = []
        for lead in leads_data:
            business_id = lead.get("business_id")
            business = (
                self.client.table("businesses")
                .select("*")
                .eq("id", business_id)
                .execute()
                .data[0]
                if business_id
                else None
            )
            analysis = (
                self.client.table("analyses")
                .select("*")
                .eq("business_id", business_id)
                .execute()
                .data[0]
                if business_id
                else None
            )
            enriched.append(
                {**lead, "businesses": business or {}, "analyses": analysis or {}}
            )

        return enriched

    def get_lead(self, lead_id: str) -> Optional[dict]:
        if not self.client:
            lead = next(
                (l for l in self._in_memory["leads"] if l["id"] == lead_id), None
            )
            if lead:
                business = next(
                    (
                        b
                        for b in self._in_memory["businesses"]
                        if b["id"] == lead.get("business_id")
                    ),
                    None,
                )
                analysis = next(
                    (
                        a
                        for a in self._in_memory["analyses"]
                        if a.get("business_id") == lead.get("business_id")
                    ),
                    None,
                )
                return {
                    **lead,
                    "businesses": business or {},
                    "analyses": analysis or {},
                }
            return None
        response = (
            self.client.table("leads")
            .select("*, businesses(*), analyses(*)")
            .eq("id", lead_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def update_lead(self, lead_id: str, data: dict) -> dict:
        if not self.client:
            for i, l in enumerate(self._in_memory["leads"]):
                if l["id"] == lead_id:
                    l.update(data)
                    l["updated_at"] = datetime.utcnow().isoformat()
                    return l
            return {"id": lead_id, **data}
        data["updated_at"] = datetime.utcnow().isoformat()
        response = self.client.table("leads").update(data).eq("id", lead_id).execute()
        return response.data[0] if response.data else data

    def delete_lead(self, lead_id: str) -> bool:
        if not self.client:
            self._in_memory["leads"] = [
                l for l in self._in_memory["leads"] if l["id"] != lead_id
            ]
            return True
        response = self.client.table("leads").delete().eq("id", lead_id).execute()
        return bool(response.data)

    def get_lead_stats(self) -> dict:
        if not self.client:
            leads = self._in_memory["leads"]
            return {
                "total": len(leads),
                "hot": sum(1 for l in leads if l.get("priority") == "hot"),
                "medium": sum(1 for l in leads if l.get("priority") == "medium"),
                "low": sum(1 for l in leads if l.get("priority") == "low"),
            }
        response = self.client.table("leads").select("priority").execute()
        leads = response.data or []
        return {
            "total": len(leads),
            "hot": sum(1 for l in leads if l.get("priority") == "hot"),
            "medium": sum(1 for l in leads if l.get("priority") == "medium"),
            "low": sum(1 for l in leads if l.get("priority") == "low"),
        }


db = Database()
