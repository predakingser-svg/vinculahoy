import os
import httpx
from mcp.server.mcpserver import MCPServer

app = MCPServer("cloudflare-mcp")

CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
BASE_URL = "https://api.cloudflare.com/client/v4"


def get_headers() -> dict[str, str]:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", CLOUDFLARE_API_TOKEN)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@app.tool()
async def cloudflare_verify_token() -> str:
    """Verifica si el token de API de Cloudflare es válido y tiene los permisos adecuados."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/user/tokens/verify", headers=get_headers())
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                result = data.get("result", {})
                return f"Token de Cloudflare VÁLIDO!\nID: {result.get('id')}\nEstado: {result.get('status')}"
        return f"Token no válido ({res.status_code}): {res.text}"


@app.tool()
async def cloudflare_list_pages_projects(account_id: str = "") -> str:
    """Lista los proyectos existentes en Cloudflare Pages."""
    acc_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", CLOUDFLARE_ACCOUNT_ID)
    if not acc_id:
        return "Error: Se requiere CLOUDFLARE_ACCOUNT_ID para listar proyectos de Pages."

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/accounts/{acc_id}/pages/projects", headers=get_headers())
        if res.status_code == 200:
            projects = res.json().get("result", [])
            if not projects:
                return "No hay proyectos de Cloudflare Pages creados en esta cuenta."
            lines = [f"- {p['name']} (Subdominio: {p.get('subdomain')}, Producción: {p.get('production_branch')})" for p in projects]
            return "Proyectos de Cloudflare Pages:\n" + "\n".join(lines)
        return f"Error ({res.status_code}): {res.text}"


@app.tool()
async def cloudflare_list_zones() -> str:
    """Lista los dominios y zonas DNS gestionadas en la cuenta de Cloudflare."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/zones", headers=get_headers())
        if res.status_code == 200:
            zones = res.json().get("result", [])
            if not zones:
                return "No hay zonas DNS configuradas en esta cuenta de Cloudflare."
            lines = [f"- {z['name']} (ID: {z['id']}, Estado: {z['status']})" for z in zones]
            return "Zonas DNS en Cloudflare:\n" + "\n".join(lines)
        return f"Error ({res.status_code}): {res.text}"


if __name__ == "__main__":
    app.run(transport="stdio")
