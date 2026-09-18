from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole, VerificationStatus


# ------------------------------------------------------------------------------
# REGISTRO Y GESTIÓN DE APRENDIZ
# ------------------------------------------------------------------------------
class AprendizRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Contraseña mínima de 6 caracteres")
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = None
    skills: Optional[str] = Field(None, description="Habilidades separadas por coma o descripción libre")
    interest_area: str = Field(..., min_length=2, max_length=100, description="Área formativa de interés")
    max_commute_km: float = Field(default=5.0, ge=0.5, le=50.0, description="Radio de traslado en kilómetros")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    program_file_url: Optional[str] = Field(None, description="URL de la Ficha del Programa (PDF o Imagen)")


class AprendizProfileResponse(BaseModel):
    id: str
    full_name: str
    phone: Optional[str] = None
    skills: Optional[str] = None
    interest_area: str
    max_commute_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# REGISTRO Y GESTIÓN DE CENTRO DE TRABAJO
# ------------------------------------------------------------------------------
class WorkCenterRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    company_name: str = Field(..., min_length=2, max_length=200)
    trade: str = Field(..., min_length=2, max_length=150, description="Giro o actividad del centro")
    description: Optional[str] = None
    address: str = Field(..., min_length=5, max_length=300)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    vacancies: int = Field(default=1, ge=1, le=100, description="Número de vacantes disponibles para aprendices")
    latitude: float = Field(..., ge=-90, le=90, description="Latitud WGS84")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud WGS84")
    is_premium: bool = Field(default=False, description="Centro destacado")
    program_file_url: Optional[str] = Field(None, description="URL de la Ficha del Programa (PDF o Imagen)")


# ------------------------------------------------------------------------------
# RESPUESTAS DE USUARIOS
# ------------------------------------------------------------------------------
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    is_active: bool
    program_file_url: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    created_at: datetime
    aprendiz_profile: Optional[AprendizProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
