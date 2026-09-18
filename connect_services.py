#!/usr/bin/env python3
"""
================================================================================
VinculaHoy / RedFuturo - Asistente de Vinculación de Servicios y MCPs
================================================================================
Este script abre de forma automática las consolas oficiales de autenticación
en el navegador predeterminado del sistema operativo. Al aprovechar las sesiones
ya abiertas (Google SSO, GitHub, Supabase, Cloudflare, Render), podrás vincular
cada servicio con 1 solo clic y configurar los servidores MCP en Antigravity.
================================================================================
"""

import os
import sys
import json
import subprocess
import webbrowser
import time
from pathlib import Path

# Rutas estándar de Microsoft Edge en Windows
EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
]


def open_url_in_edge(url: str):
    """
    Abre la URL específicamente en Microsoft Edge para aprovechar
    las sesiones y cuentas de Google/GitHub/Supabase ya abiertas allí.
    """
    for edge_exe in EDGE_PATHS:
        if os.path.exists(edge_exe):
            try:
                subprocess.Popen([edge_exe, url])
                return
            except Exception:
                pass

    # Fallback mediante comando del sistema Windows
    try:
        subprocess.Popen(["cmd", "/c", "start", "msedge", url], shell=True)
    except Exception:
        webbrowser.open(url)


# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "vinculahoy-backend"
ENV_FILE = BACKEND_DIR / ".env"
GLOBAL_MCP_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"
LOCAL_MCP_CONFIG = ROOT_DIR / "mcp_config.json"
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"

# URLs oficiales que aprovechan las sesiones ya iniciadas en el navegador
SERVICES = {
    "google": {
        "name": "Google Account (Gemini Ecosystem)",
        "desc": "Inicio de sesión unificado y API Key de Gemini / Antigravity",
        "url": "https://aistudio.google.com/app/apikey",
        "env_var": "GEMINI_API_KEY",
        "help": "Haz clic en 'Create API key' usando tu cuenta de Google ya abierta."
    },
    "github": {
        "name": "GitHub",
        "desc": "Clonado, control de versiones y conexión con MCP Store",
        "url": "https://github.com/settings/tokens/new?scopes=repo,read:user,workflow&description=Antigravity-VinculaHoy",
        "env_var": "GITHUB_TOKEN",
        "help": "Tu navegador detectará tu sesión de GitHub activa. Desplázate al fondo y pulsa 'Generate token'."
    },
    "supabase": {
        "name": "Supabase (PostgreSQL + PostGIS)",
        "desc": "Base de datos geoespacial (soporta login con GitHub / Google)",
        "url": "https://supabase.com/dashboard/account/tokens",
        "url_project": "https://supabase.com/dashboard",
        "env_var": "DATABASE_URL",
        "help": "Inicia sesión con 1 clic (GitHub/Google). Copia tu cadena de conexión URI (postgresql+asyncpg://...)."
    },
    "cloudflare": {
        "name": "Cloudflare",
        "desc": "CDN, Cloudflare Pages y configuración DNS",
        "url": "https://dash.cloudflare.com/profile/api-tokens",
        "env_var": "CLOUDFLARE_API_TOKEN",
        "help": "Pulsa 'Create Token', usa la plantilla 'Edit Cloudflare Workers' o 'All accounts'."
    },
    "render": {
        "name": "Render",
        "desc": "Alojamiento en la nube para el contenedor FastAPI",
        "url": "https://dashboard.render.com/u/settings#api-keys",
        "env_var": "RENDER_API_KEY",
        "help": "Tu sesión se abrirá directamente. Pulsa 'Create API Key' y dale un nombre."
    }
}


def load_env_vars() -> dict:
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def save_env_var(key: str, value: str):
    env_vars = load_env_vars()
    env_vars[key] = value
    lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
        found = False
        for line in existing_lines:
            if line.strip().startswith(f"{key}="):
                lines.append(f'{key}="{value}"\n')
                found = True
            else:
                lines.append(line)
        if not found:
            lines.append(f'{key}="{value}"\n')
    else:
        for k, v in env_vars.items():
            lines.append(f'{k}="{v}"\n')

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def generate_mcp_config():
    """
    Genera el archivo mcp_config.json apuntando a los servidores MCP en Python creados
    para GitHub, Supabase, Cloudflare y Render.
    """
    env_vars = load_env_vars()
    py_exec = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

    mcp_config = {
        "mcpServers": {
            "github": {
                "command": py_exec,
                "args": [str(BACKEND_DIR / "mcp_servers" / "github_mcp.py")],
                "env": {
                    "GITHUB_TOKEN": env_vars.get("GITHUB_TOKEN", "")
                }
            },
            "supabase": {
                "command": py_exec,
                "args": [str(BACKEND_DIR / "mcp_servers" / "supabase_mcp.py")],
                "env": {
                    "DATABASE_URL": env_vars.get("DATABASE_URL", "")
                }
            },
            "cloudflare": {
                "command": py_exec,
                "args": [str(BACKEND_DIR / "mcp_servers" / "cloudflare_mcp.py")],
                "env": {
                    "CLOUDFLARE_API_TOKEN": env_vars.get("CLOUDFLARE_API_TOKEN", ""),
                    "CLOUDFLARE_ACCOUNT_ID": env_vars.get("CLOUDFLARE_ACCOUNT_ID", "")
                }
            },
            "render": {
                "command": py_exec,
                "args": [str(BACKEND_DIR / "mcp_servers" / "render_mcp.py")],
                "env": {
                    "RENDER_API_KEY": env_vars.get("RENDER_API_KEY", "")
                }
            }
        }
    }

    # Guardar en local del proyecto
    with open(LOCAL_MCP_CONFIG, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=2)

    # Guardar en configuración global de Antigravity
    GLOBAL_MCP_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_MCP_CONFIG, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=2)

    print(f"\n[OK] Configuración MCP actualizada exitosamente en:")
    print(f"    - Global: {GLOBAL_MCP_CONFIG}")
    print(f"    - Proyecto: {LOCAL_MCP_CONFIG}")


def open_service(key: str):
    srv = SERVICES.get(key)
    if not srv:
        return

    print(f"\n" + "=" * 70)
    print(f"🌐 Conectando con: {srv['name']}")
    print(f"📖 Descripción: {srv['desc']}")
    print(f"💡 Guía: {srv['help']}")
    print(f"🚀 Abriendo específicamente en Microsoft Edge...")
    print("=" * 70)

    open_url_in_edge(srv["url"])
    time.sleep(1)

    val = input(f"\nPega el Token / Credencial para {srv['env_var']} (o presiona ENTER para omitir): ").strip()
    if val:
        save_env_var(srv["env_var"], val)
        print(f"[OK] {srv['env_var']} guardado correctamente en .env")
        generate_mcp_config()


def open_all_services():
    print("\n" + "=" * 70)
    print("🚀 Abriendo todas las plataformas en Microsoft Edge...")
    print("Edge reconocerá automáticamente tus sesiones y cuentas abiertas.")
    print("=" * 70)
    for key, srv in SERVICES.items():
        print(f"- Abriendo {srv['name']} en Microsoft Edge...")
        open_url_in_edge(srv["url"])
        time.sleep(1.2)

    print("\n[OK] Todas las páginas han sido abiertas en Microsoft Edge.")
    print("Una vez generados tus tokens, selecciona la opción para ingresarlos o editarlos en .env.")


def show_status():
    env_vars = load_env_vars()
    print("\n" + "=" * 70)
    print("📊 ESTADO ACTUAL DE VINCULACIÓN DE SERVICIOS")
    print("=" * 70)
    for key, srv in SERVICES.items():
        val = env_vars.get(srv["env_var"], "")
        if val and not val.startswith("TU_") and len(val) > 5:
            masked = val[:4] + "*" * (len(val) - 8) + val[-4:] if len(val) > 10 else "****"
            status = f"\033[92m[CONECTADO]\033[0m ({masked})"
        else:
            status = "\033[93m[PENDIENTE]\033[0m"
        print(f"• {srv['name']:<35} {status}")
    print("=" * 70)


def main():
    while True:
        show_status()
        print("\nOpciones disponibles:")
        print(" 1. Abrir TODOS los servicios en el navegador a la vez (1-Click SSO)")
        print(" 2. Conectar Google Account (Gemini Ecosystem)")
        print(" 3. Conectar GitHub")
        print(" 4. Conectar Supabase (PostgreSQL + PostGIS)")
        print(" 5. Conectar Cloudflare (Pages & DNS)")
        print(" 6. Conectar Render (FastAPI Cloud)")
        print(" 7. Regenerar archivo mcp_config.json")
        print(" 8. Salir")

        choice = input("\nSelecciona una opción (1-8): ").strip()

        if choice == "1":
            open_all_services()
        elif choice == "2":
            open_service("google")
        elif choice == "3":
            open_service("github")
        elif choice == "4":
            open_service("supabase")
        elif choice == "5":
            open_service("cloudflare")
        elif choice == "6":
            open_service("render")
        elif choice == "7":
            generate_mcp_config()
        elif choice == "8":
            print("\n¡Hasta pronto!")
            break
        else:
            print("\nOpción no válida. Intenta nuevamente.")


if __name__ == "__main__":
    main()
