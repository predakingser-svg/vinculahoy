import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VinculaHoy"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Base de Datos PostgreSQL + PostGIS (o fallback)
    DATABASE_URL: str = "sqlite+aiosqlite:///./vinculahoy.db"

    # Seguridad y JWT
    SECRET_KEY: str = "vinculahoy_super_secret_jwt_key_change_me_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # CORS para Cloudflare Pages y Desarrollo local
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        if isinstance(v, str):
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Descargo Legal Obligatorio
    LEGAL_DISCLAIMER: str = (
        "Plataforma independiente de vinculación comunitaria sin afiliación, "
        "patrocinio ni relación oficial con el Gobierno de México o el programa "
        "Jóvenes Construyendo el Futuro."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
