from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class WorkCenterResponse(BaseModel):
    id: str
    company_name: str
    trade: str
    description: Optional[str] = None
    address: str
    schedule: Optional[str] = None
    contact_person: Optional[str] = None
    rfc: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    vacancies: int
    is_verified: bool
    is_premium: bool
    is_featured: bool = Field(..., description="Bandera para destacar en carrusel de frontend (True si es premium)")
    latitude: float
    longitude: float
    distance_km: Optional[float] = Field(None, description="Distancia calculada en kilómetros respecto al punto de búsqueda")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NearbyCentersResponse(BaseModel):
    total: int
    latitude: float
    longitude: float
    radius_km: float
    legal_disclaimer: str
    centers: List[WorkCenterResponse]


# ------------------------------------------------------------------------------
# ESQUEMAS DE MENSAJERÍA / VINCULACIÓN
# ------------------------------------------------------------------------------
class ChatMessageCreate(BaseModel):
    receiver_id: str
    center_id: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=2000, description="Contenido del mensaje de postulación o consulta")


class ChatMessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    center_id: Optional[str] = None
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
