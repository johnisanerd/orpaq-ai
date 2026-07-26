import sqlite3
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import settings


DB_PATH = Path(settings.SQLITE_PATH or Path.home() / ".orpaq" / "leads.db")


class Database:
    def __init__(self):
        self._lock = threading.Lock()
        self._connection: sqlite3.Connection = None  # type: ignore

    def init(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        self._connection = conn
        self._create_tables()

    @property
    def conn(self) -> sqlite3.Connection:
        assert self._connection is not None, "Database not initialized. Call db.init() first."
        return self._connection

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                website TEXT,
                phone TEXT,
                email TEXT,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                address TEXT,
                rating REAL,
                reviews_count INTEGER,
                source TEXT DEFAULT 'google_maps',
                website_quality TEXT DEFAULT 'unknown',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                screenshot_url TEXT,
                pagespeed_score INTEGER,
                pagespeed_issues TEXT,
                mobile_friendly INTEGER,
                ai_ui_score REAL,
                ai_outdated INTEGER,
                ai_issues TEXT,
                ai_suggestions TEXT,
                analysis_status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                lead_score INTEGER NOT NULL,
                priority TEXT DEFAULT 'low',
                outreach_message TEXT,
                redesign_suggestions TEXT,
                pipeline_id TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS pipeline_requests (
                id TEXT PRIMARY KEY,
                location TEXT NOT NULL,
                category TEXT NOT NULL,
                limit_count INTEGER DEFAULT 20,
                status TEXT DEFAULT 'pending',
                result TEXT,
                error TEXT,
                requested_at TEXT,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id TEXT PRIMARY KEY,
                location TEXT,
                category TEXT,
                businesses_found INTEGER DEFAULT 0,
                businesses_stored INTEGER DEFAULT 0,
                websites_analyzed INTEGER DEFAULT 0,
                leads_generated INTEGER DEFAULT 0,
                errors TEXT,
                status TEXT DEFAULT 'running',
                started_at TEXT,
                completed_at TEXT,
                updated_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_businesses_location ON businesses(location);
            CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(category);
            CREATE INDEX IF NOT EXISTS idx_analyses_business ON analyses(business_id);
            CREATE INDEX IF NOT EXISTS idx_leads_business ON leads(business_id);
            CREATE INDEX IF NOT EXISTS idx_leads_priority ON leads(priority);
            CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score);
            CREATE INDEX IF NOT EXISTS idx_pipeline_requests_status ON pipeline_requests(status);
        """)
        self.conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _new_id(self) -> str:
        return str(uuid.uuid4())

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> dict:
        if row is None:
            return {}
        return dict(row)

    def _rows_to_list(self, rows: list[sqlite3.Row]) -> list[dict]:
        return [dict(r) for r in rows]

    # ─── Business CRUD ───────────────────────────────────────────────

    def create_business(self, data: dict) -> dict:
        with self._lock:
            now = self._now()
            row_id = self._new_id()
            self.conn.execute(
                """INSERT INTO businesses (id, name, website, phone, email, category, location,
                   address, rating, reviews_count, source, website_quality, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row_id,
                    data.get("name", ""),
                    data.get("website"),
                    data.get("phone"),
                    data.get("email"),
                    data.get("category", ""),
                    data.get("location", ""),
                    data.get("address"),
                    data.get("rating"),
                    data.get("reviews_count"),
                    data.get("source", "google_maps"),
                    data.get("website_quality", "unknown"),
                    now,
                    now,
                ),
            )
            self.conn.commit()
            return {
                "id": row_id,
                **{k: v for k, v in data.items() if k != "id"},
                "created_at": now,
                "updated_at": now,
            }

    def get_business(self, business_id: str) -> Optional[dict]:
        cur = self.conn.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def get_businesses(
        self, location: Optional[str] = None, category: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        sql = "SELECT * FROM businesses WHERE 1=1"
        params = []
        if location:
            sql += " AND LOWER(location) LIKE ?"
            params.append(f"%{location.lower()}%")
        if category:
            sql += " AND LOWER(category) = ?"
            params.append(category.lower())
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.execute(sql, params)
        return self._rows_to_list(cur.fetchall())

    def update_business(self, business_id: str, data: dict) -> dict:
        now = self._now()
        fields = {k: v for k, v in data.items() if k != "id"}
        fields["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [business_id]
        self.conn.execute(f"UPDATE businesses SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return {"id": business_id, **data, "updated_at": now}

    # ─── Analysis CRUD ──────────────────────────────────────────────

    def create_analysis(self, data: dict) -> dict:
        with self._lock:
            now = self._now()
            row_id = self._new_id()
            # Serialize list/dict fields to JSON
            pagespeed_issues = data.get("pagespeed_issues")
            ai_issues = data.get("ai_issues")
            if isinstance(pagespeed_issues, (list, dict)):
                pagespeed_issues = json.dumps(pagespeed_issues)
            if isinstance(ai_issues, (list, dict)):
                ai_issues = json.dumps(ai_issues)

            self.conn.execute(
                """INSERT INTO analyses (id, business_id, screenshot_url, pagespeed_score,
                   pagespeed_issues, mobile_friendly, ai_ui_score, ai_outdated, ai_issues,
                   ai_suggestions, analysis_status, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row_id,
                    data.get("business_id"),
                    data.get("screenshot_url"),
                    data.get("pagespeed_score"),
                    pagespeed_issues,
                    1 if data.get("mobile_friendly") else 0,
                    data.get("ai_ui_score"),
                    1 if data.get("ai_outdated") else 0,
                    ai_issues,
                    data.get("ai_suggestions"),
                    data.get("analysis_status", "completed"),
                    now,
                    now,
                ),
            )
            self.conn.commit()
            return {
                "id": row_id,
                **{k: v for k, v in data.items() if k != "id"},
                "created_at": now,
                "updated_at": now,
            }

    def get_analysis(self, business_id: str) -> Optional[dict]:
        cur = self.conn.execute(
            "SELECT * FROM analyses WHERE business_id = ? ORDER BY created_at DESC LIMIT 1",
            (business_id,),
        )
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def update_analysis(self, analysis_id: str, data: dict) -> dict:
        now = self._now()
        fields = {k: v for k, v in data.items() if k != "id"}
        fields["updated_at"] = now
        # Deserialize for storage
        for key in ("pagespeed_issues", "ai_issues"):
            if key in fields and isinstance(fields[key], (list, dict)):
                fields[key] = json.dumps(fields[key])
        for key in ("mobile_friendly", "ai_outdated"):
            if key in fields:
                fields[key] = 1 if fields[key] else 0
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [analysis_id]
        self.conn.execute(f"UPDATE analyses SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return {"id": analysis_id, **data, "updated_at": now}

    # ─── Lead CRUD ──────────────────────────────────────────────────

    def create_lead(self, data: dict) -> dict:
        with self._lock:
            now = self._now()
            row_id = self._new_id()
            self.conn.execute(
                """INSERT INTO leads (id, business_id, lead_score, priority, outreach_message,
                   redesign_suggestions, pipeline_id, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    row_id,
                    data.get("business_id"),
                    data.get("lead_score", 0),
                    data.get("priority", "low"),
                    data.get("outreach_message"),
                    data.get("redesign_suggestions"),
                    data.get("pipeline_id"),
                    now,
                    now,
                ),
            )
            self.conn.commit()
            return {
                "id": row_id,
                **{k: v for k, v in data.items() if k != "id"},
                "created_at": now,
                "updated_at": now,
            }

    def get_leads(self, filters: Optional[dict] = None, limit: int = 100) -> list[dict]:
        sql = """SELECT l.*, b.id as b_id, b.name as b_name, b.website as b_website,
                 b.phone as b_phone, b.email as b_email, b.category as b_category,
                 b.location as b_location, b.address as b_address, b.rating as b_rating,
                 b.reviews_count as b_reviews_count, b.source as b_source,
                 a.id as a_id, a.pagespeed_score as a_pagespeed_score,
                 a.mobile_friendly as a_mobile_friendly, a.ai_ui_score as a_ai_ui_score,
                 a.ai_outdated as a_ai_outdated, a.ai_issues as a_ai_issues,
                 a.ai_suggestions as a_ai_suggestions, a.screenshot_url as a_screenshot_url,
                 a.analysis_status as a_analysis_status
                 FROM leads l
                 LEFT JOIN businesses b ON l.business_id = b.id
                 LEFT JOIN analyses a ON a.business_id = l.business_id
                 WHERE 1=1"""
        params = []
        if filters:
            if "priority" in filters and filters["priority"]:
                sql += " AND l.priority = ?"
                params.append(filters["priority"])
            if "min_score" in filters and filters["min_score"] is not None:
                sql += " AND l.lead_score >= ?"
                params.append(filters["min_score"])
            if "max_score" in filters and filters["max_score"] is not None:
                sql += " AND l.lead_score <= ?"
                params.append(filters["max_score"])
            if filters.get("has_website") is not None:
                if filters["has_website"]:
                    sql += " AND b.website IS NOT NULL AND b.website != ''"
                else:
                    sql += " AND (b.website IS NULL OR b.website = '')"
            if filters.get("location"):
                sql += " AND LOWER(b.location) LIKE ?"
                params.append(f"%{filters['location'].lower()}%")
            if filters.get("category"):
                sql += " AND LOWER(b.category) = ?"
                params.append(filters["category"].lower())
            if filters.get("search"):
                sql += " AND LOWER(b.name) LIKE ?"
                params.append(f"%{filters['search'].lower()}%")
        sql += " ORDER BY l.lead_score DESC LIMIT ?"
        params.append(limit)

        cur = self.conn.execute(sql, params)
        rows = cur.fetchall()
        enriched = []
        for row in rows:
            d = dict(row)
            enriched.append(
                {
                    "id": d["id"],
                    "business_id": d["business_id"],
                    "lead_score": d["lead_score"],
                    "priority": d["priority"],
                    "outreach_message": d["outreach_message"],
                    "redesign_suggestions": d["redesign_suggestions"],
                    "pipeline_id": d["pipeline_id"],
                    "created_at": d["created_at"],
                    "updated_at": d["updated_at"],
                    "businesses": {
                        "id": d["b_id"],
                        "name": d["b_name"],
                        "website": d["b_website"],
                        "phone": d["b_phone"],
                        "email": d["b_email"],
                        "category": d["b_category"],
                        "location": d["b_location"],
                        "address": d["b_address"],
                        "rating": d["b_rating"],
                        "reviews_count": d["b_reviews_count"],
                        "source": d["b_source"],
                    }
                    if d.get("b_id")
                    else {},
                    "analyses": {
                        "id": d["a_id"],
                        "pagespeed_score": d["a_pagespeed_score"],
                        "mobile_friendly": bool(d["a_mobile_friendly"]) if d.get("a_mobile_friendly") is not None else None,
                        "ai_ui_score": d["a_ai_ui_score"],
                        "ai_outdated": bool(d["a_ai_outdated"]) if d.get("a_ai_outdated") is not None else None,
                        "ai_issues": json.loads(d["a_ai_issues"]) if d.get("a_ai_issues") else None,
                        "ai_suggestions": d["a_ai_suggestions"],
                        "screenshot_url": d["a_screenshot_url"],
                        "analysis_status": d["a_analysis_status"],
                    }
                    if d.get("a_id")
                    else {},
                }
            )
        return enriched

    def get_lead(self, lead_id: str) -> Optional[dict]:
        leads = self.get_leads(limit=1000)
        for lead in leads:
            if lead["id"] == lead_id:
                return lead
        return None

    def update_lead(self, lead_id: str, data: dict) -> dict:
        now = self._now()
        fields = {k: v for k, v in data.items() if k != "id"}
        fields["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [lead_id]
        self.conn.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return {"id": lead_id, **data, "updated_at": now}

    def delete_lead(self, lead_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_lead_stats(self) -> dict:
        cur = self.conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN priority='hot' THEN 1 ELSE 0 END) as hot, "
            "SUM(CASE WHEN priority='medium' THEN 1 ELSE 0 END) as medium, "
            "SUM(CASE WHEN priority='low' THEN 1 ELSE 0 END) as low "
            "FROM leads"
        )
        row = cur.fetchone()
        return dict(row) if row else {"total": 0, "hot": 0, "medium": 0, "low": 0}

    # ─── Pipeline Requests ──────────────────────────────────────────

    def create_pipeline_request(self, location: str, category: str, limit_count: int = 20) -> dict:
        with self._lock:
            now = self._now()
            row_id = self._new_id()
            self.conn.execute(
                "INSERT INTO pipeline_requests (id, location, category, limit_count, status, requested_at) VALUES (?,?,?,?,?,?)",
                (row_id, location, category, limit_count, "pending", now),
            )
            self.conn.commit()
            return {"id": row_id, "location": location, "category": category, "limit_count": limit_count, "status": "pending", "requested_at": now}

    def get_pending_pipeline_requests(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM pipeline_requests WHERE status = 'pending' ORDER BY requested_at ASC LIMIT 10"
        )
        return self._rows_to_list(cur.fetchall())

    def update_pipeline_request(self, req_id: str, status: str, result: Optional[str] = None, error: Optional[str] = None):
        now = self._now()
        self.conn.execute(
            "UPDATE pipeline_requests SET status=?, result=?, error=?, completed_at=? WHERE id=?",
            (status, result, error, now, req_id),
        )
        self.conn.commit()

    # ─── Pipeline Runs ──────────────────────────────────────────────

    def create_pipeline_run(self, location: str, category: str) -> str:
        with self._lock:
            now = self._now()
            row_id = self._new_id()
            self.conn.execute(
                "INSERT INTO pipeline_runs (id, location, category, status, started_at) VALUES (?,?,?,?,?)",
                (row_id, location, category, "running", now),
            )
            self.conn.commit()
            return row_id

    def update_pipeline_run(self, run_id: str, **kwargs):
        now = self._now()
        kwargs["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [run_id]
        self.conn.execute(f"UPDATE pipeline_runs SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def get_pipeline_runs(self, limit: int = 20) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        )
        return self._rows_to_list(cur.fetchall())


db = Database()
