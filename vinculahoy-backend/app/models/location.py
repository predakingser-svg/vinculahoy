import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement
from app.database import Base
from app.config import settings


def make_geo_point(longitude: float, latitude: float):
    """
    Retorna un WKTElement para PostGIS (PostgreSQL) o texto plano WKT para SQLite.
    """
    point_wkt = f"POINT({longitude} {latitude})"
    if "postgresql" in settings.DATABASE_URL:
        return WKTElement(point_wkt, srid=4326)
    return point_wkt


class WorkCenter(Base):
    """
    Modelo de Centro de Trabajo con geolocalización PostGIS y soporte para modelo Freemium.
    """
    __tablename__ = "work_centers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    company_name = Column(String(200), nullable=False, index=True)
    trade = Column(String(150), nullable=False, index=True)  # Giro del centro
    description = Column(Text, nullable=True)
    address = Column(String(300), nullable=False)
    schedule = Column(String(100), nullable=True)  # Horario formativo
    contact_person = Column(String(150), nullable=True)  # Persona / tutor de contacto
    rfc = Column(String(20), nullable=True)  # RFC o identificación fiscal
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Plazas de formación para aprendices
    vacancies = Column(Integer, default=1, nullable=False)
    
    # Verificación oficial del centro
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    
    # Modelo Freemium: los centros premium tienen prioridad visual y geográfica
    is_premium = Column(Boolean, default=False, nullable=False, index=True)
    
    # Coordenadas numéricas directas para renderizado rápido en frontend Leaflet
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Ubicación geoespacial nativa PostGIS (WGS 84 EPSG:4326)
    # Permite ST_DWithin y ST_Distance en metros de forma precisa sobre el esferoide
    # Soporta with_variant para compatibilidad en SQLite durante pruebas locales
    location = Column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False).with_variant(Text, "sqlite"),
        nullable=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    @property
    def is_featured(self) -> bool:
        return bool(self.is_premium)

    # Relaciones
    user = relationship("User", back_populates="work_center")
    inquiries = relationship("ChatMessage", back_populates="center", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Mensajería directa entre un Aprendiz y un Centro de Trabajo.
    """
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    center_id = Column(String(36), ForeignKey("work_centers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    center = relationship("WorkCenter", back_populates="inquiries")
