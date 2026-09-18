import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from mcp.server.mcpserver import MCPServer

app = MCPServer("supabase-mcp")

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", DATABASE_URL)
    # Asegurar driver asyncpg si es postgres
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@app.tool()
async def supabase_test_connection() -> str:
    """Verifica la conectividad con la base de datos PostgreSQL de Supabase o fallback local SQLite."""
    url = get_db_url()
    if not url:
        return "Error: DATABASE_URL no está configurada en las variables de entorno."

    try:
        engine = create_async_engine(url, echo=False)
        async with engine.connect() as conn:
            if "sqlite" in url:
                result = await conn.execute(text("SELECT sqlite_version();"))
                ver = result.scalar()
                return (
                    f"Conexión exitosa a base de datos local SQLite (Modo desarrollo / Fallback)!\n"
                    f"Versión SQLite: {ver}\n"
                    f"Nota: Para conectar a Supabase en la nube, actualiza DATABASE_URL en .env con tu URI de PostgreSQL."
                )
            result = await conn.execute(text("SELECT version();"))
            ver = result.scalar()
            return f"Conexión exitosa a Supabase PostgreSQL!\nVersión: {ver}"
    except Exception as e:
        return f"Fallo al conectar con la base de datos: {str(e)}"


@app.tool()
async def supabase_verify_postgis() -> str:
    """Verifica si la extensión espacial PostGIS está instalada y activa en la base de datos."""
    url = get_db_url()
    if "sqlite" in url:
        return (
            "Base de datos actual: SQLite local (vinculahoy.db).\n"
            "PostGIS requiere PostgreSQL en Supabase.\n"
            "En entorno local se utiliza cálculo euclidiano / Haversine; al migrar a Supabase estará activo PostGIS."
        )
    try:
        engine = create_async_engine(url, echo=False)
        async with engine.connect() as conn:
            # Consultar versiones de extensiones instaladas
            result = await conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'postgis';"))
            row = result.fetchone()
            if row:
                # Obtener versión detallada de PostGIS
                try:
                    full_ver = (await conn.execute(text("SELECT PostGIS_Full_Version();"))).scalar()
                    return f"Extensión PostGIS ACTIVA (v{row[1]})\nDetalles: {full_ver}"
                except Exception:
                    return f"Extensión PostGIS ACTIVA (v{row[1]})."
            else:
                return (
                    "La extensión PostGIS NO está habilitada aún.\n"
                    "Puedes habilitarla ejecutando en el SQL Editor de Supabase:\n"
                    "CREATE EXTENSION IF NOT EXISTS postgis;"
                )
    except Exception as e:
        return f"Error al consultar PostGIS: {str(e)}"


@app.tool()
async def supabase_list_tables() -> str:
    """Lista las tablas y vistas en el esquema público o base de datos actual."""
    url = get_db_url()
    try:
        engine = create_async_engine(url, echo=False)
        async with engine.connect() as conn:
            if "sqlite" in url:
                query = text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%' 
                    ORDER BY name;
                """)
                result = await conn.execute(query)
                tables = [r[0] for r in result.fetchall()]
                if not tables:
                    return "No hay tablas creadas en la base de datos local."
                return "Tablas encontradas en SQLite local:\n" + "\n".join(f"- {t}" for t in tables)
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            result = await conn.execute(query)
            tables = [r[0] for r in result.fetchall()]
            if not tables:
                return "No hay tablas creadas en el esquema 'public'."
            return "Tablas encontradas en Supabase:\n" + "\n".join(f"- {t}" for t in tables)
    except Exception as e:
        return f"Error al listar tablas: {str(e)}"


@app.tool()
async def supabase_execute_sql(sql_query: str) -> str:
    """Ejecuta una consulta SQL en la base de datos (SELECT, CREATE TABLE, etc.) y retorna los resultados."""
    url = get_db_url()
    try:
        engine = create_async_engine(url, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text(sql_query))
            if result.returns_rows:
                rows = result.fetchmany(25)
                headers = list(result.keys())
                out = [f"Columnas: {', '.join(headers)}"]
                for r in rows:
                    out.append(str(dict(r._mapping)))
                return "\n".join(out)
            else:
                await conn.commit()
                return "Consulta ejecutada exitosamente (0 filas retornadas)."
    except Exception as e:
        return f"Error SQL: {str(e)}"


if __name__ == "__main__":
    app.run(transport="stdio")
