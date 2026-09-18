import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, cast
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_SetSRID, ST_MakePoint

from app.database import get_db
from app.config import settings
from app.models.location import WorkCenter
from app.schemas.location import NearbyCentersResponse, WorkCenterResponse

router = APIRouter(prefix="/centers", tags=["Centros de Trabajo & Geolocalización"])


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Cálculo auxiliar de distancia Haversine en kilómetros entre dos coordenadas WGS84.
    Utilizado para ordenamiento de respaldo o verificación de precisión.
    """
    R = 6371.0  # Radio de la Tierra en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


@router.get("/nearby", response_model=NearbyCentersResponse)
async def get_nearby_centers(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitud GPS del aprendiz"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitud GPS del aprendiz"),
    radius_km: float = Query(5.0, gt=0.1, le=100.0, description="Radio de búsqueda en kilómetros"),
    trade: Optional[str] = Query(None, description="Filtrar por giro comercial o formativo"),
    db: AsyncSession = Depends(get_db)
):
    """
    Búsqueda geoespacial de Centros de Trabajo cercanos usando PostGIS (ST_DWithin y ST_Distance).
    
    Estrategia de Priorización de Negocio (Freemium):
    1. Centros con `is_premium = True` se ordenan primero (con bandera `is_featured = True`).
    2. Posteriormente se ordenan por proximidad métrica (distancia en km ascendente).
    """
    radius_meters = radius_km * 1000.0
    centers_result: List[WorkCenterResponse] = []

    try:
        # ----------------------------------------------------------------------
        # CONSULTA NATIVA POSTGIS (SUPABASE)
        # ----------------------------------------------------------------------
        # Punto del aprendiz en WGS84 EPSG:4326 convertido a Geography
        user_point_geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        user_point_geog = cast(user_point_geom, Geography)

        # Expresión de distancia en metros calculada por el esferoide PostGIS
        dist_expr = ST_Distance(WorkCenter.location, user_point_geog)

        # Consulta con filtro ST_DWithin para máxima eficiencia espacial con índices R-Tree
        query = (
            select(
                WorkCenter,
                dist_expr.label("distance_meters")
            )
            .where(
                ST_DWithin(WorkCenter.location, user_point_geog, radius_meters)
            )
        )

        if trade:
            query = query.where(WorkCenter.trade.ilike(f"%{trade}%"))

        # Priorización Freemium: is_premium primero, luego distancia más corta
        query = query.order_by(
            desc(WorkCenter.is_premium),
            asc("distance_meters")
        )

        result = await db.execute(query)
        rows = result.all()

        for center, dist_m in rows:
            dist_km = round(dist_m / 1000.0, 2) if dist_m is not None else None
            centers_result.append(
                WorkCenterResponse(
                    id=center.id,
                    company_name=center.company_name,
                    trade=center.trade,
                    description=center.description,
                    address=center.address,
                    contact_email=center.contact_email,
                    contact_phone=center.contact_phone,
                    vacancies=center.vacancies,
                    is_verified=center.is_verified,
                    is_premium=center.is_premium,
                    is_featured=center.is_premium,  # Bandera Freemium
                    latitude=center.latitude,
                    longitude=center.longitude,
                    distance_km=dist_km,
                    created_at=center.created_at
                )
            )

    except Exception as exc:
        # ----------------------------------------------------------------------
        # FALLBACK HAVERSINE (Para entornos de desarrollo locales sin PostGIS)
        # ----------------------------------------------------------------------
        print(f"[Aviso] Ejecutando fallback de cálculo Haversine: {exc}")
        base_query = select(WorkCenter)
        if trade:
            base_query = base_query.where(WorkCenter.trade.ilike(f"%{trade}%"))

        all_centers = (await db.scalars(base_query)).all()
        calculated_centers = []

        for center in all_centers:
            d_km = haversine_distance_km(latitude, longitude, center.latitude, center.longitude)
            if d_km <= radius_km:
                calculated_centers.append((center, d_km))

        # Ordenar: is_premium primero (True > False), luego menor distancia
        calculated_centers.sort(key=lambda item: (not item[0].is_premium, item[1]))

        for center, d_km in calculated_centers:
            centers_result.append(
                WorkCenterResponse(
                    id=center.id,
                    company_name=center.company_name,
                    trade=center.trade,
                    description=center.description,
                    address=center.address,
                    contact_email=center.contact_email,
                    contact_phone=center.contact_phone,
                    vacancies=center.vacancies,
                    is_verified=center.is_verified,
                    is_premium=center.is_premium,
                    is_featured=center.is_premium,
                    latitude=center.latitude,
                    longitude=center.longitude,
                    distance_km=d_km,
                    created_at=center.created_at
                )
            )

    return NearbyCentersResponse(
        total=len(centers_result),
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        legal_disclaimer=settings.LEGAL_DISCLAIMER,
        centers=centers_result
    )


@router.get("/{center_id}", response_model=WorkCenterResponse)
async def get_center_by_id(center_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retorna el detalle completo de un Centro de Trabajo por su identificador único.
    """
    center = await db.scalar(select(WorkCenter).where(WorkCenter.id == center_id))
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centro de Trabajo no encontrado"
        )
    return WorkCenterResponse(
        id=center.id,
        company_name=center.company_name,
        trade=center.trade,
        description=center.description,
        address=center.address,
        contact_email=center.contact_email,
        contact_phone=center.contact_phone,
        vacancies=center.vacancies,
        is_verified=center.is_verified,
        is_premium=center.is_premium,
        is_featured=center.is_premium,
        latitude=center.latitude,
        longitude=center.longitude,
        distance_km=None,
        created_at=center.created_at
    )
