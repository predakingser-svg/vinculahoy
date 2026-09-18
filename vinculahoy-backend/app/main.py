import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.api import api_router
from app.models.user import User, UserRole
from app.models.location import WorkCenter, make_geo_point
from app.core.security import get_password_hash


async def seed_initial_data():
    """
    Puebla la base de datos con centros de trabajo de prueba si se encuentra vacía,
    incluyendo centros estándar y centros destacados (Freemium: is_premium = True).
    """
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(WorkCenter))
        if count is not None:
            return  # Ya existen datos

        print("[Seed] Creando centros de trabajo iniciales de prueba...")

        # Coordenadas en Ciudad de México para pruebas inmediatas
        sample_centers = [
            {
                "company_name": "TechInnovadores México (SaaS & Cloud)",
                "trade": "Tecnología de la Información",
                "description": "Formación integral en desarrollo web, soporte en la nube y análisis de datos para aprendices proactivos.",
                "address": "Av. Insurgentes Sur 601, Nápoles, Benito Juárez, CDMX",
                "contact_email": "rh@techinnovadores.mx",
                "contact_phone": "+52 55 1234 5678",
                "vacancies": 4,
                "is_verified": True,
                "is_premium": True,  # DESTACADO FREEMIUM
                "latitude": 19.3954,
                "longitude": -99.1728
            },
            {
                "company_name": "Taller Creativo Gráfico & Digital",
                "trade": "Diseño y Publicidad",
                "description": "Capacitación práctica en diseño editorial, redes sociales y producción gráfica.",
                "address": "Colima 180, Roma Norte, Cuauhtémoc, CDMX",
                "contact_email": "hola@tallercreativo.mx",
                "contact_phone": "+52 55 8765 4321",
                "vacancies": 2,
                "is_verified": True,
                "is_premium": True,  # DESTACADO FREEMIUM
                "latitude": 19.4187,
                "longitude": -99.1623
            },
            {
                "company_name": "Consultoría Contable & Financiera Juárez",
                "trade": "Administración y Finanzas",
                "description": "Aprende facturación electrónica, control de inventarios y contabilidad general para PYMEs.",
                "address": "Paseo de la Reforma 250, Juárez, Cuauhtémoc, CDMX",
                "contact_email": "contacto@juarezcontable.com",
                "contact_phone": "+52 55 5555 9999",
                "vacancies": 3,
                "is_verified": True,
                "is_premium": False,
                "latitude": 19.4290,
                "longitude": -99.1620
            },
            {
                "company_name": "Café de Especialidad & Repostería Artesanal",
                "trade": "Servicios y Alimentos",
                "description": "Formación en barismo, servicio al cliente y repostería de alta gama.",
                "address": "Michoacán 72, Condesa, Cuauhtémoc, CDMX",
                "contact_email": "baristas@cafecito.mx",
                "contact_phone": "+52 55 4433 2211",
                "vacancies": 2,
                "is_verified": False,
                "is_premium": False,
                "latitude": 19.4115,
                "longitude": -99.1742
            },
            {
                "company_name": "Taller Mecánico & Diagnóstico Automotriz Pro",
                "trade": "Oficios y Mantenimiento",
                "description": "Diagnóstico por computadora, mecánica preventiva y electromecánica automotriz.",
                "address": "Eje Central Lázaro Cárdenas 412, Álamos, Benito Juárez, CDMX",
                "contact_email": "soporte@mecanicapro.mx",
                "contact_phone": "+52 55 7788 9900",
                "vacancies": 5,
                "is_verified": True,
                "is_premium": False,
                "latitude": 19.3980,
                "longitude": -99.1450
            }
        ]

        for i, item in enumerate(sample_centers, start=1):
            center_user = User(
                email=item["contact_email"],
                hashed_password=get_password_hash("VinculaHoy2026!"),
                role=UserRole.CENTRO_TRABAJO,
                is_active=True
            )
            session.add(center_user)
            await session.flush()

            geo_point = make_geo_point(item['longitude'], item['latitude'])

            center = WorkCenter(
                user_id=center_user.id,
                company_name=item["company_name"],
                trade=item["trade"],
                description=item["description"],
                address=item["address"],
                contact_email=item["contact_email"],
                contact_phone=item["contact_phone"],
                vacancies=item["vacancies"],
                is_verified=item["is_verified"],
                is_premium=item["is_premium"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                location=geo_point
            )
            session.add(center)

        await session.commit()
        print("[Seed] 5 centros de trabajo creados exitosamente.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Ciclo de vida de la aplicación: inicializa modelos de BD con tabla 100% vacía en producción.
    """
    print(f"[*] Iniciando {settings.PROJECT_NAME}...")
    try:
        await init_db()
        # BASE DE DATOS 100% VACÍA: No se ejecutan datos de prueba (seed data)
        print("[*] Base de datos verificada y lista (100% vacía para producción).")
    except Exception as exc:
        print(f"[Aviso] No se pudo inicializar la BD durante el arranque: {exc}")
    yield
    print(f"[*] Deteniendo {settings.PROJECT_NAME}...")


app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    version="1.0.0",
    description=(
        f"API Backend de Vinculación Comunitaria y Geolocalización PostGIS.\n\n"
        f"**Aviso Legal:** {settings.LEGAL_DISCLAIMER}"
    ),
    lifespan=lifespan
)

# ------------------------------------------------------------------------------
# MIDDLEWARE CORS (Cloudflare Pages y Clientes Frontend)
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# MIDDLEWARE DE HEADERS DE SEGURIDAD (Cloudflare WAF / Security Headers)
# ------------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ------------------------------------------------------------------------------
# REGISTRO DE RUTAS API
# ------------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Información"])
async def root():
    """
    Endpoint raíz con metadatos del servicio y descargo de responsabilidad obligatorio.
    """
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
        "legal_disclaimer": settings.LEGAL_DISCLAIMER
    }


@app.get("/api/v1/metadata", tags=["Información"])
async def metadata():
    """
    Retorna información y marco legal de la plataforma para clientes frontend.
    """
    return {
        "project": settings.PROJECT_NAME,
        "environment": "development" if settings.DEBUG else "production",
        "legal_disclaimer": settings.LEGAL_DISCLAIMER,
        "supported_roles": ["APRENDIZ", "CENTRO_TRABAJO"],
        "geo_srid": 4326,
        "default_radius_km": 5.0
    }


# ------------------------------------------------------------------------------
# MONTAJE DE ARCHIVOS ESTÁTICOS Y SUBIDAS (Fichas del programa)
# ------------------------------------------------------------------------------
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "program_files"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# ------------------------------------------------------------------------------
# MONTAJE DE FRONTEND ESTÁTICO (Para ejecución local directa)
# ------------------------------------------------------------------------------
# Busca la carpeta frontend en el nivel superior
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    @app.get("/app", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
