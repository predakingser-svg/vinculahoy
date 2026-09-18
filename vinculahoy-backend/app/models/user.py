import uuid
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserRole(str, Enum):
    APRENDIZ = "APRENDIZ"
    CENTRO_TRABAJO = "CENTRO_TRABAJO"
    ADMIN = "ADMIN"


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role_enum"), default=UserRole.APRENDIZ, nullable=False)
    program_file_url = Column(String(500), nullable=True)  # Ficha del Programa (PDF o Imagen)
    verification_status = Column(
        SQLEnum(VerificationStatus, name="verification_status_enum"),
        default=VerificationStatus.PENDING,
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones 1 a 1 según el rol
    aprendiz_profile = relationship("AprendizProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    work_center = relationship("WorkCenter", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Mensajes enviados y recibidos
    sent_messages = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender", cascade="all, delete-orphan")
    received_messages = relationship("ChatMessage", foreign_keys="ChatMessage.receiver_id", back_populates="receiver", cascade="all, delete-orphan")


class AprendizProfile(Base):
    __tablename__ = "aprendiz_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(30), nullable=True)
    skills = Column(Text, nullable=True)  # Ej. "Python, Atención a clientes, Excel"
    interest_area = Column(String(100), nullable=False, index=True)  # Ej. "Tecnología", "Administración"
    max_commute_km = Column(Float, default=5.0, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="aprendiz_profile")
