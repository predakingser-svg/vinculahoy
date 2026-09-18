from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings

# Determinar argumentos específicos por motor (ej. SQLite no soporta ciertos pool settings)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Motor asíncrono de SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args=connect_args
)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base declarativa para modelos
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Inyector de dependencias FastAPI para obtener sesiones asíncronas de base de datos.
    Garantiza el cierre automático de la conexión tras responder a la petición.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializa las extensiones (PostGIS si es PostgreSQL) y crea las tablas declaradas.
    """
    async with engine.begin() as conn:
        # Habilitar PostGIS si estamos en PostgreSQL
        if "postgresql" in settings.DATABASE_URL:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            except Exception as e:
                print(f"[Aviso] No se pudo verificar la extensión PostGIS automáticamente: {e}")

        # Crear todas las tablas
        await conn.run_sync(Base.metadata.create_all)
