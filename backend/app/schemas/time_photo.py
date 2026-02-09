from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Create request ────────────────────────────────────────────────────────────────

class TimePhotoCreate(BaseModel):
    target_year: int = Field(..., ge=1800, le=2030, description="Target historical year")
    apply_era_style: bool = Field(True, description="Apply era-appropriate visual style (legacy)")
    mode: Optional[str] = Field(None, description="Transformation mode: clothing_only, full, full_vintage")


# ── Single photo response ─────────────────────────────────────────────────────────

class TimePhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_image_url: str
    result_image_url: Optional[str] = None
    target_year: int
    apply_era_style: bool
    style_applied: Optional[str] = None
    prompt_used: Optional[str] = None
    geminigen_uuid: Optional[str] = None
    provider: Optional[str] = "geminigen"
    transformation_mode: Optional[str] = "full_vintage"
    status: str
    error_message: Optional[str] = None
    cost: int
    created_at: datetime
    completed_at: Optional[datetime] = None


# ── Paginated history ───────────────────────────────────────────────────────────

class TimePhotoHistory(BaseModel):
    items: List[TimePhotoOut]
    total: int
    page: int
    per_page: int
    pages: int


# ── Crystal balance ─────────────────────────────────────────────────────────────

class CrystalBalance(BaseModel):
    chrono_crystals: int
    how_to_earn: List[str] = [
        "Завершайте маршруты — +1 кристалл за каждый маршрут",
        "Проходите квизы без ошибок — +1 кристалл",
        "Ежедневный бонус за серию (streak) — +1 кристалл",
        "Получайте достижения — до +3 кристаллов",
        "Приглашайте друзей — +2 кристалла за каждого",
    ]


# ── Time Machine configuration ─────────────────────────────────────────────────

class TransformationMode(BaseModel):
    id: str
    name: str
    desc: str


class TimeMachineConfig(BaseModel):
    provider: str = "geminigen"  # Current provider: "geminigen" or "kie"
    mode: str = "full_vintage"   # Current default mode
    modes: List[Dict[str, str]]  # Available modes with descriptions
