# VinculaHoy (RedFuturo) - Plataforma de Vinculación Comunitaria

> **Descargo de Responsabilidad Legal Obligatorio:**  
> VinculaHoy es una plataforma independiente de vinculación comunitaria sin afiliación, patrocinio ni relación oficial con el Gobierno de México o el programa Jóvenes Construyendo el Futuro.

---

## 🌟 Visión del Proyecto
**VinculaHoy** es un MVP de arquitectura moderna de **costo $0 USD** diseñado para conectar a aprendices y centros de trabajo cercanos utilizando geolocalización de alta precisión (PostGIS) y un modelo Freemium que destaca a empresas verificadas y premium.

---

## 📁 Estructura del Repositorio

```text
.
├── vinculahoy-backend/           # API REST construida con FastAPI y PostGIS
│   ├── app/
│   │   ├── api/                  # Endpoints (/auth, /centers, /chat)
│   │   ├── core/                 # Criptografía Bcrypt y seguridad JWT
│   │   ├── models/               # Modelos SQLAlchemy y GeoAlchemy2 PostGIS
│   │   ├── schemas/              # Validación Pydantic v2 y Type Hints
│   │   ├── config.py             # Variables de entorno con pydantic-settings
│   │   ├── database.py           # Conexión asíncrona SQLAlchemy (Supabase / SQLite)
│   │   └── main.py               # Entrypoint FastAPI con CORS y middlewares
│   ├── .env.example              # Configuración de variables de entorno
│   ├── requirements.txt          # Dependencias fijadas para Python 3.11+
│   └── README.md                 # Guía técnica específica del Backend
│
└── frontend/                     # SPA estática optimizada para Cloudflare Pages
    ├── index.html                # Interfaz responsiva con Tailwind CSS y Leaflet.js
    ├── app.js                    # Consumo de API, radar GPS y renderizado de mapa
    ├── styles.css                # Estilos visuales de marcadores y animaciones
    ├── _headers                  # Cabeceras de seguridad y caché HTTP para Cloudflare
    └── _routes.json              # Configuración de enrutamiento Cloudflare Pages
```

---

## 🚀 Inicio Rápido en 3 Pasos

### 1. Iniciar el Backend (FastAPI)
```bash
cd vinculahoy-backend

# Crear y activar entorno virtual
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor local
uvicorn app.main:app --reload --port 8000
```
- **Documentación Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Frontend local integrado:** [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)

---

### 2. Configuración de Base de Datos en Supabase (PostGIS)
1. En tu proyecto de [Supabase](https://supabase.com), abre el **SQL Editor**.
2. Ejecuta:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. En `vinculahoy-backend/.env`, coloca tu URL de conexión:
   ```env
   DATABASE_URL="postgresql+asyncpg://postgres:TU_PASSWORD@db.TU_PROYECTO.supabase.co:5432/postgres"
   ```

---

### 3. Despliegue en Cloudflare Pages
1. Conecta este repositorio en el panel de **Cloudflare Pages**.
2. Establece el **Build output directory** como `frontend`.
3. ¡Listo! Cloudflare distribuirá tu aplicación a nivel global con SSL automático y costo $0 USD.
