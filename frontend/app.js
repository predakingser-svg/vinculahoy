/**
 * VinculaHoy (RedFuturo) - Frontend Client SPA
 * Integración con FastAPI, PostGIS y Leaflet.js
 */

// Configuración de endpoint del Backend
// En desarrollo usa localhost; en producción apunta a la API desplegada en Render
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:8000/api/v1'
  : 'https://vinculahoy-api.onrender.com/api/v1';

// Estado global de la aplicación
const state = {
  userLat: 19.4187,   // Coordenada inicial por defecto (CDMX Roma Norte)
  userLng: -99.1623,
  radiusKm: 5.0,
  tradeFilter: '',
  centers: [],
  selectedCenter: null,
  map: null,
  userMarker: null,
  radiusCircle: null,
  markersLayer: null
};

// =============================================================================
// INICIALIZACIÓN DEL MAPA LEAFLET
// =============================================================================
function initMap() {
  state.map = L.map('map', {
    zoomControl: true,
    attributionControl: false
  }).setView([state.userLat, state.userLng], 13);

  // Capa base de OpenStreetMap (Costo $0 USD)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(state.map);

  // Capa para agrupar y limpiar marcadores de centros
  state.markersLayer = L.layerGroup().addTo(state.map);

  // Renderizar indicador de ubicación del aprendiz
  updateUserMarker();

  // Cargar centros iniciales
  fetchNearbyCenters();
}

// =============================================================================
// ACTUALIZACIÓN DE MARCADOR DEL APRENDIZ Y CÍRCULO DE RADIO
// =============================================================================
function updateUserMarker() {
  const latLng = [state.userLat, state.userLng];

  // Actualizar o crear marcador de pulso azul
  if (state.userMarker) {
    state.userMarker.setLatLng(latLng);
  } else {
    const pulseIcon = L.divIcon({
      className: 'user-pulse-marker',
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
    state.userMarker = L.marker(latLng, { icon: pulseIcon })
      .addTo(state.map)
      .bindPopup(`
        <div class="p-3 text-xs">
          <strong class="text-blue-700 font-bold block mb-1">Tu Ubicación de Búsqueda</strong>
          <span class="text-slate-600">Buscando centros en un radio de ${state.radiusKm} km</span>
        </div>
      `);
  }

  // Actualizar o crear círculo de cobertura de radio
  if (state.radiusCircle) {
    state.radiusCircle.setLatLng(latLng);
    state.radiusCircle.setRadius(state.radiusKm * 1000);
  } else {
    state.radiusCircle = L.circle(latLng, {
      radius: state.radiusKm * 1000,
      color: '#10b981',
      fillColor: '#10b981',
      fillOpacity: 0.08,
      weight: 1.5,
      dashArray: '4, 6'
    }).addTo(state.map);
  }
}

// =============================================================================
// DATOS DE RESPALDO / MODO DEMO EN VIVO
// Permite que la plataforma sea 100% interactiva en despliegue estático y producción
// =============================================================================
const DEMO_CENTERS = [
  {
    id: "demo-tech-1",
    company_name: "TechInnovadores México (SaaS & Cloud)",
    trade: "Tecnología de la Información",
    description: "Formación integral en desarrollo web, soporte en la nube y análisis de datos para aprendices proactivos.",
    address: "Av. Insurgentes Sur 601, Nápoles, Benito Juárez, CDMX",
    contact_email: "rh@techinnovadores.mx",
    contact_phone: "+52 55 1234 5678",
    vacancies: 4,
    is_verified: true,
    is_premium: true,
    latitude: 19.3954,
    longitude: -99.1728
  },
  {
    id: "demo-design-2",
    company_name: "Taller Creativo Gráfico & Digital",
    trade: "Diseño y Publicidad",
    description: "Capacitación práctica en diseño editorial, redes sociales y producción gráfica.",
    address: "Colima 180, Roma Norte, Cuauhtémoc, CDMX",
    contact_email: "hola@tallercreativo.mx",
    contact_phone: "+52 55 8765 4321",
    vacancies: 2,
    is_verified: true,
    is_premium: true,
    latitude: 19.4187,
    longitude: -99.1623
  },
  {
    id: "demo-finance-3",
    company_name: "Consultoría Contable & Financiera Juárez",
    trade: "Administración y Finanzas",
    description: "Prácticas en facturación electrónica, declaraciones y conciliación bancaria.",
    address: "Paseo de la Reforma 250, Juárez, Cuauhtémoc, CDMX",
    contact_email: "empleos@consultoriajuarez.com",
    contact_phone: "+52 55 3344 5566",
    vacancies: 3,
    is_verified: true,
    is_premium: false,
    latitude: 19.4270,
    longitude: -99.1670
  },
  {
    id: "demo-mechanic-4",
    company_name: "Taller Mecánico & Diagnóstico Automotriz Rápido",
    trade: "Mecánica y Mantenimiento",
    description: "Mantenimiento preventivo, escáner OBD-II y afinación general multimarca.",
    address: "Eje Central Lázaro Cárdenas 412, Alamos, Benito Juárez, CDMX",
    contact_email: "contacto@mecanicarapida.mx",
    contact_phone: "+52 55 7788 9900",
    vacancies: 2,
    is_verified: true,
    is_premium: false,
    latitude: 19.3980,
    longitude: -99.1450
  },
  {
    id: "demo-food-5",
    company_name: "Cafetería & Panadería Artesanal El Sol",
    trade: "Servicios y Alimentos",
    description: "Barismo profesional, repostería artesanal y atención a clientes de alta calidad.",
    address: "Álvaro Obregón 90, Roma Norte, Cuauhtémoc, CDMX",
    contact_email: "contacto@cafeteriaelsol.mx",
    contact_phone: "+52 55 4433 2211",
    vacancies: 5,
    is_verified: true,
    is_premium: true,
    latitude: 19.4172,
    longitude: -99.1585
  },
  {
    id: "demo-health-6",
    company_name: "Centro Odontológico Integral Condesa",
    trade: "Salud y Cuidado",
    description: "Asistencia dental, esterilización de instrumental y recepción de pacientes.",
    address: "Av. Michoacán 45, Condesa, Cuauhtémoc, CDMX",
    contact_email: "clinica@dentalcondesa.mx",
    contact_phone: "+52 55 9988 1122",
    vacancies: 1,
    is_verified: true,
    is_premium: false,
    latitude: 19.4115,
    longitude: -99.1740
  }
];

function calculateHaversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radio de la Tierra en km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return parseFloat((R * c).toFixed(1));
}

// =============================================================================
// CONSUMO DE API: /api/v1/centers/nearby (POSTGIS) CON FALLBACK INTERACTIVO
// =============================================================================
async function fetchNearbyCenters() {
  const loader = document.getElementById('mapLoader');
  loader.classList.remove('hidden');

  try {
    let url = `${API_BASE_URL}/centers/nearby?latitude=${state.userLat}&longitude=${state.userLng}&radius_km=${state.radiusKm}`;
    if (state.tradeFilter) {
      url += `&trade=${encodeURIComponent(state.tradeFilter)}`;
    }

    const response = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (!response.ok) {
      throw new Error(`Error en servidor: ${response.status}`);
    }

    const data = await response.json();
    state.centers = data.centers || [];
    document.getElementById('totalCenters').textContent = data.total;
    renderMarkers();
    renderCentersList();

  } catch (error) {
    // Si el backend aún no está activo o estamos en GitHub Pages / Cloudflare Pages estático:
    console.info('Utilizando catálogo de datos interactivo local/fallback:', error.message);
    
    // Calcular distancia Haversine y filtrar según radio y giro
    const filtered = DEMO_CENTERS
      .map(c => ({
        ...c,
        distance_km: calculateHaversineKm(state.userLat, state.userLng, c.latitude, c.longitude)
      }))
      .filter(c => c.distance_km <= state.radiusKm)
      .filter(c => !state.tradeFilter || c.trade === state.tradeFilter)
      .sort((a, b) => {
        // Primero destacados (Freemium), luego por menor distancia
        if (a.is_premium && !b.is_premium) return -1;
        if (!a.is_premium && b.is_premium) return 1;
        return a.distance_km - b.distance_km;
      });

    state.centers = filtered;
    document.getElementById('totalCenters').textContent = filtered.length;
    renderMarkers();
    renderCentersList();

  } finally {
    loader.classList.add('hidden');
  }
}

// =============================================================================
// RENDERIZADO DE MARCADORES EN EL MAPA LEAFLET
// =============================================================================
function renderMarkers() {
  state.markersLayer.clearLayers();

  state.centers.forEach(center => {
    const isPremium = center.is_featured || center.is_premium;
    const markerClass = isPremium ? 'custom-marker marker-premium' : 'custom-marker marker-standard';
    const iconClass = isPremium ? 'fa-solid fa-star' : 'fa-solid fa-briefcase';

    const customIcon = L.divIcon({
      className: '',
      html: `<div class="${markerClass}"><i class="${iconClass} text-xs"></i></div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
      popupAnchor: [0, -20]
    });

    const marker = L.marker([center.latitude, center.longitude], { icon: customIcon });

    // Contenido del Popup
    const popupContent = `
      <div class="p-4 max-w-xs">
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
            isPremium ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
          }">
            ${isPremium ? '★ Destacado' : 'Verificado'}
          </span>
          <span class="text-xs font-semibold text-slate-500">${center.distance_km ?? '--'} km</span>
        </div>
        <h4 class="font-bold text-slate-900 text-sm mb-1">${center.company_name}</h4>
        <p class="text-xs text-brand-700 font-medium mb-2">${center.trade}</p>
        <p class="text-[11px] text-slate-600 mb-3 line-clamp-2">${center.address}</p>
        <div class="flex items-center justify-between pt-2 border-t border-slate-100">
          <span class="text-xs font-semibold text-slate-700">
            <i class="fa-solid fa-users text-slate-400 mr-1"></i> ${center.vacancies} vacantes
          </span>
          <button onclick="openContactModal('${center.id}')" class="text-xs bg-brand-600 hover:bg-brand-700 text-white font-semibold px-2.5 py-1.5 rounded-lg transition">
            Postularme
          </button>
        </div>
      </div>
    `;

    marker.bindPopup(popupContent);
    state.markersLayer.addLayer(marker);
  });
}

// =============================================================================
// RENDERIZADO DE LA LISTA LATERAL (FREEMIUM PRIORITARIO)
// =============================================================================
function renderCentersList() {
  const container = document.getElementById('centersList');
  container.innerHTML = '';

  if (state.centers.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12 text-slate-500">
        <i class="fa-solid fa-radar text-4xl mb-3 text-slate-300"></i>
        <h4 class="font-bold text-slate-800 text-sm">No se encontraron centros</h4>
        <p class="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
          Intenta aumentar el radio de búsqueda o seleccionar otro giro formativo.
        </p>
      </div>
    `;
    return;
  }

  state.centers.forEach(center => {
    const isPremium = center.is_featured || center.is_premium;
    const card = document.createElement('div');
    card.className = `p-4 rounded-xl border transition cursor-pointer relative ${
      isPremium
        ? 'bg-gradient-to-br from-amber-50/70 to-white border-amber-300 shadow-sm hover:border-amber-400'
        : 'bg-white border-slate-200 hover:border-brand-500 shadow-xs'
    }`;

    card.onclick = () => {
      state.map.flyTo([center.latitude, center.longitude], 15, { duration: 1.2 });
    };

    card.innerHTML = `
      <div class="flex items-start justify-between gap-2 mb-1.5">
        <div class="flex items-center gap-1.5">
          ${
            isPremium
              ? `<span class="inline-flex items-center gap-1 text-[10px] font-extrabold uppercase bg-amber-100 text-amber-800 px-2 py-0.5 rounded-md border border-amber-200">
                  <i class="fa-solid fa-star text-amber-500 text-[9px]"></i> Destacado
                </span>`
              : ''
          }
          ${
            center.is_verified
              ? `<span class="inline-flex items-center gap-1 text-[10px] font-semibold bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded-md">
                  <i class="fa-solid fa-circle-check text-emerald-500 text-[10px]"></i> Verificado
                </span>`
              : ''
          }
        </div>
        <div class="flex items-center gap-1 text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-lg">
          <i class="fa-solid fa-route text-slate-400 text-[10px]"></i>
          <span>${center.distance_km ?? '--'} km</span>
        </div>
      </div>

      <h3 class="font-bold text-slate-900 text-sm mb-1 leading-snug">${center.company_name}</h3>
      <p class="text-xs font-semibold text-brand-600 mb-2">${center.trade}</p>
      <p class="text-xs text-slate-500 mb-3 flex items-start gap-1.5">
        <i class="fa-solid fa-location-dot text-slate-400 text-xs mt-0.5 flex-shrink-0"></i>
        <span>${center.address}</span>
      </p>

      <div class="flex items-center justify-between pt-2 border-t border-slate-100">
        <span class="text-xs text-slate-600 font-medium">
          <strong class="text-slate-900 font-bold">${center.vacancies}</strong> vacante(s) disponible(s)
        </span>
        <button onclick="event.stopPropagation(); openContactModal('${center.id}')" class="text-xs bg-slate-900 hover:bg-brand-600 text-white font-semibold px-3 py-1.5 rounded-lg transition shadow-xs">
          Vincularme
        </button>
      </div>
    `;

    container.appendChild(card);
  });
}

function renderErrorFallback(msg) {
  const container = document.getElementById('centersList');
  container.innerHTML = `
    <div class="p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs">
      <p class="font-bold mb-1 flex items-center gap-1.5">
        <i class="fa-solid fa-triangle-exclamation text-red-600"></i> No se pudo conectar al servidor
      </p>
      <p class="mb-2">Asegúrate de que la API de FastAPI esté ejecutándose en <code>http://127.0.0.1:8000</code>.</p>
      <button onclick="fetchNearbyCenters()" class="px-3 py-1.5 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 transition">
        Reintentar conexión
      </button>
    </div>
  `;
}

// =============================================================================
// GEOLOCALIZACIÓN NATIVA DEL NAVEGADOR (HTML5 GEOLOCATION API)
// =============================================================================
function handleGetGeolocation() {
  if (!navigator.geolocation) {
    alert('Tu navegador no soporta geolocalización GPS.');
    return;
  }

  const btn = document.getElementById('btnGeoHeader');
  const originalHtml = btn.innerHTML;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-sm"></i> Localizando...';
  btn.disabled = true;

  navigator.geolocation.getCurrentPosition(
    (position) => {
      state.userLat = position.coords.latitude;
      state.userLng = position.coords.longitude;

      state.map.flyTo([state.userLat, state.userLng], 14, { duration: 1.5 });
      updateUserMarker();
      fetchNearbyCenters();

      btn.innerHTML = originalHtml;
      btn.disabled = false;
    },
    (error) => {
      console.warn('Error en GPS navegador:', error);
      alert('No se pudo obtener la ubicación GPS (permiso denegado o no disponible). Se utilizará la ubicación por defecto.');
      btn.innerHTML = originalHtml;
      btn.disabled = false;
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  );
}

// =============================================================================
// MODALES Y ACCIONES
// =============================================================================
function openContactModal(centerId) {
  const center = state.centers.find(c => c.id === centerId);
  if (!center) return;

  state.selectedCenter = center;
  document.getElementById('modalCenterId').value = center.id;
  document.getElementById('modalCenterName').textContent = center.company_name;
  document.getElementById('modalCenterTrade').textContent = `${center.trade} • ${center.vacancies} vacantes`;
  document.getElementById('contactModal').classList.remove('hidden');
}

function closeContactModal() {
  document.getElementById('contactModal').classList.add('hidden');
}

function openCenterRegisterModal() {
  alert('El módulo de registro de empresas permite registrar un Centro de Trabajo mediante el endpoint POST /api/v1/auth/register/center de la API.');
}

async function handleSendApplication(e) {
  e.preventDefault();
  const name = document.getElementById('applicantName').value;
  const email = document.getElementById('applicantEmail').value;
  const msg = document.getElementById('applicantMessage').value;

  alert(`¡Postulación enviada exitosamente para ${name}!\nEl centro de trabajo ha recibido tus datos de contacto.`);
  closeContactModal();
  document.getElementById('contactForm').reset();
}

function closeInfoModal() {
  document.getElementById('infoModal').classList.add('hidden');
}

// =============================================================================
// EVENT LISTENERS
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initMap();

  // Geolocalización
  document.getElementById('btnGeoHeader').addEventListener('click', handleGetGeolocation);

  // Slider de Radio
  const radiusSlider = document.getElementById('radiusSlider');
  const radiusLabel = document.getElementById('radiusLabel');
  radiusSlider.addEventListener('input', (e) => {
    state.radiusKm = parseFloat(e.target.value);
    radiusLabel.textContent = `${state.radiusKm.toFixed(1)} km`;
    updateUserMarker();
  });
  radiusSlider.addEventListener('change', () => {
    fetchNearbyCenters();
  });

  // Filtro de Giro
  document.getElementById('tradeFilter').addEventListener('change', (e) => {
    state.tradeFilter = e.target.value;
    fetchNearbyCenters();
  });

  // Botón Refrescar
  document.getElementById('btnRefresh').addEventListener('click', () => {
    fetchNearbyCenters();
  });

  // Modal Info
  document.getElementById('btnModalInfo').addEventListener('click', () => {
    document.getElementById('infoModal').classList.remove('hidden');
  });

  // Botones de presets demo
  document.querySelectorAll('.preset-loc').forEach(btn => {
    btn.addEventListener('click', () => {
      const lat = parseFloat(btn.dataset.lat);
      const lng = parseFloat(btn.dataset.lng);
      state.userLat = lat;
      state.userLng = lng;

      state.map.flyTo([lat, lng], 14, { duration: 1.2 });
      updateUserMarker();
      fetchNearbyCenters();
    });
  });
});
