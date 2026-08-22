from collections import Counter
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.supabase import supabase

router = APIRouter(prefix="/management", tags=["Management"])


class SettingsUpdate(BaseModel):
    review_threshold: int = Field(ge=300, le=900)
    auto_refresh_minutes: int = Field(ge=1, le=120)
    email_notifications: bool
    weekly_report: bool


DEFAULT_SETTINGS = {
    "id": "default",
    "review_threshold": 650,
    "auto_refresh_minutes": 15,
    "email_notifications": True,
    "weekly_report": True,
}


@router.get("/analytics")
def analytics():
    try:
        response = supabase.table("loan_applications").select("status, created_at").execute()
        rows = response.data or []
        status_counts = Counter(row.get("status", "SUBMITTED") for row in rows)
        reviewed = status_counts["APPROVED"] + status_counts["REJECTED"]
        monthly = Counter()
        for row in rows:
            created_at = row.get("created_at")
            if created_at:
                month = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%b")
                monthly[month] += 1

        return {
            "summary": {
                "total": len(rows),
                "approved": status_counts["APPROVED"],
                "pending": status_counts["SUBMITTED"] + status_counts["UNDER_REVIEW"],
                "rejected": status_counts["REJECTED"],
                "approval_rate": round(status_counts["APPROVED"] / reviewed * 100) if reviewed else 0,
            },
            "monthly": [{"label": month, "applications": monthly[month]} for month in sorted(monthly)],
        }
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Analytics unavailable: {error}") from error


@router.get("/settings")
def get_settings():
    try:
        response = supabase.table("lender_settings").select("*").eq("id", "default").maybe_single().execute()
        return response.data or DEFAULT_SETTINGS
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Settings unavailable: {error}") from error


@router.put("/settings")
def save_settings(settings: SettingsUpdate):
    try:
        response = supabase.table("lender_settings").upsert({"id": "default", **settings.model_dump()}).execute()
        return response.data[0] if response.data else {"id": "default", **settings.model_dump()}
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Settings could not be saved: {error}") from error
