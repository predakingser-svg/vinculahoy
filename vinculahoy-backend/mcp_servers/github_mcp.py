import os
import httpx
from mcp.server.mcpserver import MCPServer

app = MCPServer("github-mcp")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
BASE_URL = "https://api.github.com"


def get_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Antigravity-VinculaHoy-MCP"
    }
    token = os.environ.get("GITHUB_TOKEN", GITHUB_TOKEN)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@app.tool()
async def github_get_user() -> str:
    """Obtiene el perfil y estado de autenticación del usuario actual de GitHub."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/user", headers=get_headers())
        if res.status_code == 200:
            data = res.json()
            return f"Usuario: {data.get('login')}\nNombre: {data.get('name')}\nRepositorios públicos: {data.get('public_repos')}\nURL: {data.get('html_url')}"
        return f"Error ({res.status_code}): {res.text}"


@app.tool()
async def github_list_repos(limit: int = 10) -> str:
    """Lista los repositorios recientes del usuario autenticado en GitHub."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/user/repos?sort=updated&per_page={limit}", headers=get_headers())
        if res.status_code == 200:
            repos = res.json()
            lines = [f"- {r['name']} ({r['html_url']}) [{'Privado' if r['private'] else 'Público'}]" for r in repos]
            return "\n".join(lines) if lines else "No se encontraron repositorios."
        return f"Error ({res.status_code}): {res.text}"


@app.tool()
async def github_create_repo(name: str, description: str = "", private: bool = False) -> str:
    """Crea un nuevo repositorio en la cuenta del usuario autenticado en GitHub."""
    payload = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": True
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/user/repos", json=payload, headers=get_headers())
        if res.status_code in (200, 201):
            data = res.json()
            return f"Repositorio creado exitosamente: {data.get('html_url')}\nClonar: {data.get('clone_url')}"
        return f"Error al crear repositorio ({res.status_code}): {res.text}"


if __name__ == "__main__":
    app.run(transport="stdio")
