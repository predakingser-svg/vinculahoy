from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.models.user import User, UserRole, AprendizProfile
from app.models.location import WorkCenter, make_geo_point
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import AprendizRegister, WorkCenterRegister, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register/aprendiz", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_aprendiz(payload: AprendizRegister, db: AsyncSession = Depends(get_db)):
    """
    Registro para aprendices del programa Jóvenes Construyendo el Futuro.
    Crea la cuenta de usuario y su perfil formativo con habilidades y radio de movilidad.
    """
    # Verificar si el correo ya existe
    existing_user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )

    # Crear usuario base
    new_user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
        role=UserRole.APRENDIZ,
        is_active=True
    )
    db.add(new_user)
    await db.flush()

    # Crear perfil de aprendiz
    profile = AprendizProfile(
        user_id=new_user.id,
        full_name=payload.full_name,
        phone=payload.phone,
        skills=payload.skills,
        interest_area=payload.interest_area,
        max_commute_km=payload.max_commute_km,
        latitude=payload.latitude,
        longitude=payload.longitude
    )
    db.add(profile)
    await db.commit()

    # Generar Token de acceso
    access_token = create_access_token(data={"sub": new_user.id, "role": new_user.role.value})
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=new_user.role.value,
        user_id=new_user.id,
        email=new_user.email
    )


@router.post("/register/center", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_work_center(payload: WorkCenterRegister, db: AsyncSession = Depends(get_db)):
    """
    Registro para Centros de Trabajo (empresas, talleres, comercios y organizaciones).
    Registra coordenadas geográficas y geolocalización PostGIS para búsqueda por radio.
    """
    existing_user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )

    new_user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
        role=UserRole.CENTRO_TRABAJO,
        is_active=True
    )
    db.add(new_user)
    await db.flush()

    # Punto geográfico PostGIS (formato: Longitud Latitud en WGS84)
    geo_point = make_geo_point(payload.longitude, payload.latitude)

    center = WorkCenter(
        user_id=new_user.id,
        company_name=payload.company_name,
        trade=payload.trade,
        description=payload.description,
        address=payload.address,
        contact_email=payload.contact_email or payload.email,
        contact_phone=payload.contact_phone,
        vacancies=payload.vacancies,
        is_verified=False,
        is_premium=payload.is_premium,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location=geo_point
    )
    db.add(center)
    await db.commit()

    access_token = create_access_token(data={"sub": new_user.id, "role": new_user.role.value})
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=new_user.role.value,
        user_id=new_user.id,
        email=new_user.email
    )


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Autentica al usuario (Aprendiz o Centro) y genera un token JWT firmado.
    """
    user = await db.scalar(select(User).where(User.email == credentials.email.lower()))
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas: verifique su correo o contraseña"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta se encuentra inactiva"
        )

    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        email=user.email
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Retorna los datos del usuario actualmente autenticado.
    """
    return current_user
