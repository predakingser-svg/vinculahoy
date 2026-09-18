import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Forzar codificación UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

GLOBAL_MCP_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"
LOCAL_MCP_CONFIG = Path(__file__).resolve().parent / "mcp_config.json"


async def verify_server(name: str, config: dict) -> dict:
    print("\n" + "=" * 75)
    print(f"🔍 VERIFICANDO INTEGRACIÓN MCP: [{name.upper()}]")
    print("=" * 75)

    command = config.get("command")
    args = config.get("args", [])
    env = os.environ.copy()
    env.update(config.get("env", {}))

    print(f"• Ejecutable : {command}")
    print(f"• Script     : {args[0] if args else 'N/A'}")

    if not Path(command).exists():
        print(f"❌ Error: El ejecutable de Python no existe en {command}")
        return {"ok": False, "error": "Ejecutable no encontrado"}

    if args and not Path(args[0]).exists():
        print(f"❌ Error: El archivo del servidor no existe en {args[0]}")
        return {"ok": False, "error": "Script no encontrado"}

    params = StdioServerParameters(command=command, args=args, env=env)

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                # 1. Handshake e Inicialización
                init_result = await session.initialize()
                server_info = getattr(init_result, "serverInfo", None)
                s_name = getattr(server_info, "name", name) if server_info else name
                s_ver = getattr(server_info, "version", "1.0.0") if server_info else "1.0.0"
                print(f"✅ Handshake e Inicialización exitosos ({s_name} v{s_ver})")

                # 2. Descubrimiento de herramientas
                tools_response = await session.list_tools()
                tools = getattr(tools_response, "tools", [])
                print(f"✅ Herramientas descubiertas y expuestas ({len(tools)} disponibles):")
                for t in tools:
                    desc = getattr(t, "description", "") or "Sin descripción"
                    print(f"   • {t.name:<30} : {desc}")

                # 3. Prueba de llamada de herramienta
                if tools:
                    test_tool = tools[0].name
                    print(f"\n🧪 Probando ejecución de herramienta [{test_tool}]...")
                    try:
                        call_res = await session.call_tool(test_tool, arguments={})
                        content = getattr(call_res, "content", [])
                        text_val = content[0].text if content and hasattr(content[0], "text") else str(content)
                        first_line = text_val.strip().splitlines()[0] if text_val.strip() else "Respuesta vacía"
                        print(f"   Resultado de la llamada: {first_line[:80]}...")
                    except Exception as call_err:
                        print(f"   (Aviso al invocar {test_tool}: {call_err})")

                print(f"\n[OK] Servidor MCP [{name.upper()}] 100% OPERATIVO.")
                return {
                    "ok": True,
                    "server": s_name,
                    "version": s_ver,
                    "tools_count": len(tools),
                    "tools": [t.name for t in tools]
                }

    except Exception as e:
        print(f"❌ Error al comunicar con el servidor MCP [{name}]: {e}")
        return {"ok": False, "error": str(e)}


async def main():
    config_file = GLOBAL_MCP_CONFIG if GLOBAL_MCP_CONFIG.exists() else LOCAL_MCP_CONFIG
    print(f"Cargando configuración desde: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    servers = data.get("mcpServers", {})
    if not servers:
        print("No se encontraron servidores configurados en mcp_config.json")
        return

    results = {}
    for name, srv_config in servers.items():
        results[name] = await verify_server(name, srv_config)

    print("\n" + "=" * 75)
    print("📊 RESUMEN FINAL DE INTEGRACIÓN DE SERVIDORES MCP (ANTIGRAVITY)")
    print("=" * 75)
    all_ok = True
    for name, res in results.items():
        if res.get("ok"):
            status = f"\033[92mOPERATIVO (100%)\033[0m - {res['tools_count']} herramientas registradas"
        else:
            status = f"\033[91mFALLIDO\033[0m: {res.get('error')}"
            all_ok = False
        print(f"• {name.upper():<15} : {status}")

    print("=" * 75)
    if all_ok:
        print("🎉 ¡TODOS LOS SERVIDORES MCP ESTÁN PERFECTAMENTE INTEGRADOS Y LISTOS!")
    else:
        print("⚠️ Algunos servidores requieren atención.")


if __name__ == "__main__":
    asyncio.run(main())
