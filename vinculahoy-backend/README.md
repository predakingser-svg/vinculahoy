# VinculaHoy (RedFuturo) - Backend API

> **Descargo de Responsabilidad Legal Obligatorio:**  
> VinculaHoy es una plataforma independiente de vinculación comunitaria sin afiliación, patrocinio ni relación oficial con el Gobierno de México o el programa Jóvenes Construyendo el Futuro.

---

## 📌 Descripción General

**VinculaHoy** es una plataforma de costo $0 USD diseñada para conectar de forma anticipada y geolocalizada a aprendices con centros de trabajo cercanos utilizando **FastAPI**, **PostgreSQL con PostGIS (Supabase Free Tier)** y una SPA ligera desplegable en **Cloudflare Pages**.

### Características Principales
- 📍 **Búsqueda Geoespacial PostGIS**: Consultas métricas mediante `ST_DWithin` y cálculo de distancias reales con `ST_Distance` sobre el esferoide WGS 84 (`EPSG:4326`).
- ⭐ **Modelo Freemium con Priorización**: Los centros con suscripción destacada (`is_premium = True` / `is_featured = True`) aparecen en primer orden en los resultados y con distintivos especiales en el mapa.
- 🔐 **Autenticación JWT Segura**: Hash con algoritmo Bcrypt y tokens de acceso para roles `APRENDIZ` y `CENTRO_TRABAJO`.
- 💬 **Módulo de Vinculación y Mensajería**: Intercambio directo de mensajes y postulaciones entre aprendices y centros de trabajo.
- ⚡ **Rendimiento Asíncrono de Alto Nivel**: Construido 100% con `async/await` en Python 3.11+, SQLAlchemy 2.0 y `asyncpg`.

---

## 🛠️ Pila Tecnológica ($0 USD)

| Componente | Tecnología | Proveedor / Nivel Gratuito |
| :--- | :--- | :--- |
| **Backend** | FastAPI + Pydantic v2 | Python 3.11+ (Render / Fly.io / Railway Free) |
| **Base de Datos** | PostgreSQL 15+ con extensión PostGIS | Supabase Free Tier (500 MB) |
| **ORM Asíncrono** | SQLAlchemy 2.0 + GeoAlchemy2 + asyncpg | Open Source |
| **Seguridad** | Passlib / Bcrypt + Python-Jose (JWT) | Open Source |
| **Frontend** | HTML5 + Tailwind CSS + Leaflet.js | Cloudflare Pages (Ancho de banda ilimitado) |
| **Mapas / GPS** | OpenStreetMap Tiles + Geolocation API | Costo $0 (Sin requerir API Key de Google Maps) |

---

## 🚀 Guía de Configuración en Supabase (PostgreSQL + PostGIS)

1. Crea una cuenta gratuita en [supabase.com](https://supabase.com) y crea un nuevo proyecto.
2. Una vez creado el proyecto, ve al menú lateral izquierdo: **SQL Editor**.
3. Ejecuta la siguiente consulta para habilitar la extensión geoespacial PostGIS:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
4. Ve a **Project Settings** ➔ **Database** ➔ Sección **Connection string**.
5. Selecciona la pestaña **URI** y copia tu cadena de conexión. Modifícala para usar el driver asíncrono `postgresql+asyncpg://`:
   ```env
   DATABASE_URL="postgresql+asyncpg://postgres:[TU_PASSWORD]@db.[TU_PROYECTO].supabase.co:5432/postgres"
   ```

---

## 💻 Instalación y Ejecución Local

### 1. Clonar y crear entorno virtual
```bash
cd vinculahoy-backend

# Crear entorno virtual de Python 3.11+
python -m venv venv

# Activar entorno virtual
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux / macOS:
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Copia el archivo `.env.example` a `.env` y ajusta tus credenciales:
```bash
cp .env.example .env
```

### 4. Iniciar el servidor de desarrollo
```bash
uvicorn app.main:app --reload --port 8000
```

- Documentación interactiva Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Documentación alternativa Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- Acceso a la interfaz web integrada: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)

---

## 📡 Endpoints Principales de la API

### 1. Autenticación (`/api/v1/auth`)
- `POST /register/aprendiz`: Registro de postulantes con habilidades, intereses y radio de desplazamiento.
- `POST /register/center`: Registro de centros con geolocalización PostGIS, giro y vacantes formativas.
- `POST /login`: Inicio de sesión que emite el Token JWT con rol (`APRENDIZ` o `CENTRO_TRABAJO`).
- `GET /me`: Obtención de perfil del usuario logueado.

### 2. Centros de Trabajo & Geolocalización (`/api/v1/centers`)
- `GET /nearby?latitude=19.4187&longitude=-99.1623&radius_km=5.0`:
  Ejecuta consulta geoespacial PostGIS (`ST_DWithin` y `ST_Distance`). Retorna los centros en el radio definido ordenando primero los centros `is_premium = True` (con `is_featured: true`) y posteriormente por cercanía métrica en kilómetros.
- `GET /{center_id}`: Consulta individual detallada de un centro.

### 3. Mensajería y Vinculación (`/api/v1/chat`)
- `POST /message`: Envío de mensaje directo / solicitud de postulación.
- `GET /history/{other_user_id}`: Historial de mensajes entre usuarios.

---

## 🌐 Despliegue del Frontend en Cloudflare Pages

El directorio `frontend/` contiene una aplicación web independiente (SPA) lista para producción:

1. Inicia sesión en [dash.cloudflare.com](https://dash.cloudflare.com) y ve a **Workers & Pages**.
2. Selecciona **Create application** ➔ **Pages** ➔ **Connect to Git** (o subida directa de carpeta).
3. Selecciona la carpeta `frontend/` como directorio raíz de publicación.
4. En `frontend/app.js`, configura la URL base de tu backend (`API_BASE_URL`) apuntando a tu servidor FastAPI en producción (ej. `https://api.tudominio.com`).
5. ¡Listo! Cloudflare Pages distribuirá la interfaz estática globalmente en su red perimetral con SSL automático y costo $0 USD.
