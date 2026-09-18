import os
import httpx
from mcp.server.mcpserver import MCPServer

app = MCPServer("render-mcp")

RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "")
BASE_URL = "https://api.render.com/v1"


def get_headers() -> dict[str, str]:
    token = os.environ.get("RENDER_API_KEY", RENDER_API_KEY)
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


@app.tool()
async def render_get_owner() -> str:
    """Verifica la validez de la API Key de Render y retorna la cuenta del propietario."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/owners?limit=5", headers=get_headers())
        if res.status_code == 200:
            owners = res.json()
            if owners:
                o = owners[0].get("owner", {})
                return f"Autenticación Render EXITOSA!\nUsuario: {o.get('name')} ({o.get('email')})\nID de Propietario: {o.get('id')}"
            return "No se encontraron propietarios asociados a esta clave de Render."
        return f"Error en Render API ({res.status_code}): {res.text}"


@app.tool()
async def render_list_services() -> str:
    """Lista todos los servicios desplegados (Web Services de FastAPI, Workers, etc.) en Render."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/services?limit=20", headers=get_headers())
        if res.status_code == 200:
            services = res.json()
            if not services:
                return "No hay servicios activos en Render."
            lines = []
            for s in services:
                srv = s.get("service", {})
                lines.append(f"- {srv.get('name')} [Tipo: {srv.get('type')}] (ID: {srv.get('id')})\n  URL: {srv.get('serviceDetails', {}).get('url', 'Sin URL pública')}\n  Repo: {srv.get('repo', 'N/A')}")
            return "Servicios en Render:\n" + "\n".join(lines)
        return f"Error ({res.status_code}): {res.text}"


@app.tool()
async def render_trigger_deploy(service_id: str) -> str:
    """Dispara un despliegue automático en Render para el servicio indicado."""
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/services/{service_id}/deploys", json={"clearCache": "do_not_clear"}, headers=get_headers())
        if res.status_code in (200, 201):
            deploy = res.json()
            return f"Despliegue iniciado exitosamente!\nID: {deploy.get('id')}\nEstado: {deploy.get('status')}"
        return f"Error al disparar despliegue ({res.status_code}): {res.text}"


if __name__ == "__main__":
    app.run(transport="stdio")
