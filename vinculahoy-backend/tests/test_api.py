import pytest
import httpx
from app.main import app, seed_initial_data
from app.database import init_db


@pytest.mark.asyncio
async def test_full_pipeline():
    # 1. Inicialización
    await init_db()
    await seed_initial_data()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Root & Descargo Legal
        res = await client.get("/")
        assert res.status_code == 200
        assert "legal_disclaimer" in res.json()

        # Metadatos
        res = await client.get("/api/v1/metadata")
        assert res.status_code == 200
        assert res.json()["geo_srid"] == 4326

        # Búsqueda Geoespacial & Freemium
        res = await client.get("/api/v1/centers/nearby", params={"latitude": 19.4187, "longitude": -99.1623, "radius_km": 10.0})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] > 0
        assert data["centers"][0]["is_featured"] == data["centers"][0]["is_premium"]

        # Registro Aprendiz & JWT
        register_payload = {
            "email": "aprendiz.qa@redfuturo.mx",
            "password": "Password123!",
            "full_name": "Aprendiz QA",
            "interest_area": "Tecnología de la Información",
            "max_commute_km": 5.0
        }
        res = await client.post("/api/v1/auth/register/aprendiz", json=register_payload)
        assert res.status_code == 201
        token = res.json()["access_token"]

        # Endpoint autenticado /me
        res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["role"] == "APRENDIZ"
