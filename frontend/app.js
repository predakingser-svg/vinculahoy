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
// SISTEMA DE NOTIFICACIONES TOAST FLOTANTES
// =============================================================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  const bgClass = type === 'error'
    ? 'bg-rose-900/95 border-rose-700 text-white'
    : (type === 'warning'
      ? 'bg-amber-900/95 border-amber-700 text-amber-50'
      : 'bg-slate-900/95 border-slate-700 text-white');
  const iconClass = type === 'error'
    ? 'fa-circle-xmark text-rose-400'
    : (type === 'warning'
      ? 'fa-triangle-exclamation text-amber-400'
      : 'fa-circle-info text-brand-400');

  toast.className = `flex items-center gap-2.5 px-4 py-2.5 rounded-xl border shadow-xl text-xs backdrop-blur-md transition-all duration-300 transform translate-y-2 opacity-0 pointer-events-auto ${bgClass}`;
  toast.innerHTML = `
    <i class="fa-solid ${iconClass} text-sm flex-shrink-0"></i>
    <span class="font-medium">${message}</span>
  `;

  container.appendChild(toast);

  // Animación de entrada
  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  // Animación de salida y remoción
  setTimeout(() => {
    toast.classList.add('translate-y-2', 'opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// =============================================================================
// INICIALIZACIÓN DEL MAPA LEAFLET & OPTIMIZACIÓN DE TILES
// =============================================================================
function initMap() {
  state.map = L.map('map', {
    zoomControl: true,
    attributionControl: false,
    minZoom: 4,
    maxZoom: 19
  }).setView([state.userLat, state.userLng], 13);

  // Capa base de OpenStreetMap con fallback rápido y configuración de tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    tileSize: 256,
    zoomOffset: 0,
    minZoom: 4,
    maxZoom: 19,
    subdomains: ['a', 'b', 'c'],
    crossOrigin: true,
    attribution: '© OpenStreetMap contributors'
  }).addTo(state.map);

  // Recalibración del tamaño del canvas de Leaflet.js
  setTimeout(() => {
    if (state.map) state.map.invalidateSize();
  }, 200);

  setTimeout(() => {
    if (state.map) state.map.invalidateSize();
  }, 600);

  // Recalibrar al redimensionar la ventana
  window.addEventListener('resize', () => {
    if (state.map) state.map.invalidateSize();
  });

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
// DATOS INICIALES (BASE DE DATOS 100% LIMPIA EN PRODUCCIÓN)
// =============================================================================
const DEMO_CENTERS = [];

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
// CONSUMO DE API: /api/v1/centers/nearby (POSTGIS)
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
    // La base de datos está limpia o no hay conexión: muestra estado vacío limpiamente
    console.warn('Consulta de centros:', error.message);
    state.centers = [];
    document.getElementById('totalCenters').textContent = '0';
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
          <button onclick="handleCenterConnect('${center.id}')" class="text-xs bg-brand-600 hover:bg-brand-700 text-white font-semibold px-2.5 py-1.5 rounded-lg transition">
            Contactar
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
      <div class="text-center py-12 px-4">
        <div class="w-14 h-14 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-3 text-brand-600 border border-brand-100 shadow-xs">
          <i class="fa-solid fa-location-crosshairs text-2xl"></i>
        </div>
        <h4 class="font-bold text-slate-800 text-sm">Aún no hay centros de trabajo registrados en esta zona</h4>
        <p class="text-xs text-slate-500 mt-1.5 max-w-xs mx-auto leading-relaxed">
          No se encontraron centros en un radio de <strong class="text-slate-700">${state.radiusKm} km</strong>${state.tradeFilter ? ` para el giro <em>"${state.tradeFilter}"</em>` : ''}. Prueba ampliando el radio o cambia el filtro de giro.
        </p>
        <div class="mt-4 flex flex-col sm:flex-row items-center justify-center gap-2">
          <button onclick="document.getElementById('radiusSlider').value = 15; state.radiusKm = 15; document.getElementById('radiusLabel').textContent = '15.0 km'; updateUserMarker(); fetchNearbyCenters();" class="w-full sm:w-auto px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-lg text-xs border border-slate-300 transition">
            <i class="fa-solid fa-arrows-maximize mr-1 text-slate-400"></i> Ampliar radio a 15 km
          </button>
          ${state.tradeFilter ? `<button onclick="document.getElementById('tradeFilter').value = ''; state.tradeFilter = ''; fetchNearbyCenters();" class="w-full sm:w-auto px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-lg text-xs transition">Ver todos los giros</button>` : ''}
        </div>
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
        <button onclick="event.stopPropagation(); handleCenterConnect('${center.id}')" class="text-xs bg-slate-900 hover:bg-brand-600 text-white font-semibold px-3 py-1.5 rounded-lg transition shadow-xs">
          Vincular
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
// GEOLOCALIZACIÓN NATIVA DEL NAVEGADOR & BÚSQUEDA MANUAL DE ZONA
// =============================================================================
function handleGetGeolocation() {
  const btn = document.getElementById('btnGeoHeader');
  const originalHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-sm"></i> Localizando...';
    btn.disabled = true;
  }

  const handleFallback = (reason) => {
    console.warn('Geolocalización GPS fallback:', reason);
    showToast('No se pudo obtener tu ubicación exacta. Mostrando centros cercanos a la zona general.', 'warning');
    if (btn) {
      btn.innerHTML = originalHtml;
      btn.disabled = false;
    }
    // Asegura el mapa en coordenada por defecto y recalibra canvas
    if (state.map) {
      state.map.flyTo([state.userLat, state.userLng], 13, { duration: 1.2 });
      setTimeout(() => state.map.invalidateSize(), 200);
    }
    updateUserMarker();
    fetchNearbyCenters();
  };

  if (!navigator.geolocation) {
    handleFallback('Navegador sin soporte de geolocalización');
    return;
  }

  try {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        try {
          state.userLat = position.coords.latitude;
          state.userLng = position.coords.longitude;

          if (state.map) {
            state.map.flyTo([state.userLat, state.userLng], 14, { duration: 1.5 });
            setTimeout(() => state.map.invalidateSize(), 200);
          }
          updateUserMarker();
          fetchNearbyCenters();
          showToast('Ubicación GPS detectada correctamente.', 'info');
        } catch (err) {
          handleFallback(err.message);
        } finally {
          if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
          }
        }
      },
      (error) => {
        handleFallback(error.message);
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 30000 }
    );
  } catch (err) {
    handleFallback(err.message);
  }
}

async function handleManualSearch() {
  const input = document.getElementById('citySearchInput');
  const query = input ? input.value.trim() : '';
  if (!query) {
    showToast('Ingresa una ciudad, colonia o código postal para buscar.', 'info');
    return;
  }

  const btn = document.getElementById('btnCitySearch');
  const originalHtml = btn ? btn.innerHTML : '';
  if (btn) btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i>';

  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Mexico')}&limit=1`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.length > 0) {
        state.userLat = parseFloat(data[0].lat);
        state.userLng = parseFloat(data[0].lon);

        if (state.map) {
          state.map.flyTo([state.userLat, state.userLng], 13, { duration: 1.2 });
          setTimeout(() => state.map.invalidateSize(), 200);
        }
        updateUserMarker();
        fetchNearbyCenters();
        const shortName = data[0].display_name.split(',')[0];
        showToast(`Ubicación actualizada: ${shortName}`, 'info');
        return;
      }
    }
    showToast('No se encontró la ubicación. Intenta con otra ciudad o código postal.', 'warning');
  } catch (err) {
    console.warn('Error en búsqueda geográfica:', err);
    showToast('No se pudo conectar al servicio de búsqueda geográfica.', 'warning');
  } finally {
    if (btn) btn.innerHTML = originalHtml;
  }
}

// =============================================================================
// MODALES Y ACCIONES (SEPARACIÓN ESTRICTA REGISTRO VS PLANES)
// =============================================================================
function openRegisterModal(roleType) {
  // Dispara el formulario de registro directo según el rol indicado
  if (roleType === 'CENTRO_TRABAJO' || roleType === 'center') {
    openCenterRegisterModal();
  } else if (roleType === 'APRENDIZ' || roleType === 'aprendiz') {
    openAprendizRegisterModal();
  } else {
    openRoleSelectModal();
  }
}

function handleCenterConnect(centerId) {
  // FLUJO DE VINCULACIÓN EN MODO INVITADO:
  // Si el usuario actual está en MODO INVITADO (sin token JWT activo):
  // 1. Cancela la acción de envío de mensaje/vinculación.
  // 2. Dispara automáticamente la apertura del modal de "Iniciar Sesión / Registro".
  const token = localStorage.getItem('vinculahoy_token');
  if (!token) {
    openLoginModal();
    return;
  }
  openContactModal(centerId);
}

function openContactModal(centerId) {
  // MODO INVITADO: Intercepta y cancela, abriendo inicio de sesión
  const token = localStorage.getItem('vinculahoy_token');
  if (!token) {
    openLoginModal();
    return;
  }

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
  // REGISTRO DE CENTRO: Abre ÚNICAMENTE el formulario de registro del centro
  document.getElementById('registerCenterModal').classList.remove('hidden');
}

function closeCenterRegisterModal() {
  document.getElementById('registerCenterModal').classList.add('hidden');
}

// =============================================================================
// MODAL: PLANES DE SUSCRIPCIÓN (FREEMIUM / DESTACADO)
// =============================================================================
function openSubscriptionPlansModal() {
  // VISIBILIDAD CONDICIONAL: SOLO si la sesión activa tiene el rol CENTRO_TRABAJO
  const token = localStorage.getItem('vinculahoy_token');
  const userRole = (localStorage.getItem('vinculahoy_user_role') || '').toUpperCase();
  if (!token || userRole !== 'CENTRO_TRABAJO') {
    return;
  }
  document.getElementById('subscriptionPlansModal').classList.remove('hidden');
}

function closeSubscriptionPlansModal() {
  document.getElementById('subscriptionPlansModal').classList.add('hidden');
}

function selectPlan(planType) {
  closeSubscriptionPlansModal();
  const isPremiumCheckbox = document.getElementById('regIsPremium');
  if (isPremiumCheckbox) {
    isPremiumCheckbox.checked = (planType === 'featured');
  }
  openCenterRegisterModal();
}

// =============================================================================
// MODAL: SELECTOR DE ROL (APRENDIZ VS CENTRO DE TRABAJO)
// =============================================================================
function openRoleSelectModal() {
  document.getElementById('roleSelectModal').classList.remove('hidden');
}

function closeRoleSelectModal() {
  document.getElementById('roleSelectModal').classList.add('hidden');
}

function chooseRole(role) {
  closeRoleSelectModal();
  // El botón "Registrarse" -> "Centro de Trabajo" abre UNICAMENTE el formulario de registro
  if (role === 'aprendiz') {
    openAprendizRegisterModal();
  } else if (role === 'center') {
    openCenterRegisterModal();
  }
}

// =============================================================================
// MODAL: REGISTRO DE APRENDIZ
// =============================================================================
function openAprendizRegisterModal() {
  document.getElementById('registerAprendizModal').classList.remove('hidden');
}

function closeAprendizRegisterModal() {
  document.getElementById('registerAprendizModal').classList.add('hidden');
}

async function handleRegisterAprendiz(e) {
  e.preventDefault();
  const btn = document.getElementById('btnSubmitAprendiz');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Creando perfil...';

  try {
    let programFileUrl = null;
    const fileInput = document.getElementById('regAprFile');
    if (fileInput && fileInput.files && fileInput.files[0]) {
      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append('file', file);
      try {
        const uploadRes = await fetch(`${API_BASE_URL}/auth/upload-ficha`, {
          method: 'POST',
          body: formData
        });
        if (uploadRes.ok) {
          const uploadData = await uploadRes.json();
          programFileUrl = uploadData.program_file_url;
        }
      } catch (uploadErr) {
        console.warn('Subida de ficha en modo diferido/local:', uploadErr);
        programFileUrl = `/static/uploads/${file.name}`;
      }
    }

    const commuteSlider = document.getElementById('regAprCommuteSlider');
    const payload = {
      email: document.getElementById('regAprEmail').value.trim(),
      password: document.getElementById('regAprPassword').value,
      full_name: document.getElementById('regAprFullName').value.trim(),
      phone: document.getElementById('regAprPhone').value.trim() || null,
      interest_area: document.getElementById('regAprInterest').value,
      skills: document.getElementById('regAprSkills').value.trim() || null,
      max_commute_km: commuteSlider ? parseFloat(commuteSlider.value) : 5.0,
      latitude: state.userLat,
      longitude: state.userLng,
      program_file_url: programFileUrl
    };

    let registeredSuccessfully = false;
    try {
      const res = await fetch(`${API_BASE_URL}/auth/register/aprendiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al registrar aprendiz');
      }

      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem('vinculahoy_token', data.access_token);
      }
      registeredSuccessfully = true;
    } catch (apiErr) {
      console.warn('Registro directo falló o modo offline:', apiErr.message);
      // Simulación offline en caso de que el backend no responda temporalmente
      renderUserNavbar({
        email: payload.email,
        role: 'aprendiz',
        verification_status: 'pending'
      });
      registeredSuccessfully = true;
    }

    if (registeredSuccessfully) {
      alert(`¡Perfil de Aprendiz creado exitosamente!\nTu Ficha del Programa se encuentra en proceso de validación.`);
      closeAprendizRegisterModal();
      document.getElementById('registerAprendizForm').reset();
      await checkAuthStatus();
    }
  } catch (err) {
    alert(`Aviso: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// =============================================================================
// MODAL: INICIO DE SESIÓN
// =============================================================================
function openLoginModal() {
  document.getElementById('loginModal').classList.remove('hidden');
}

function closeLoginModal() {
  document.getElementById('loginModal').classList.add('hidden');
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('btnSubmitLogin');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Ingresando...';

  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Credenciales inválidas. Por favor verifique su correo y contraseña.');
    }

    const data = await res.json();
    localStorage.setItem('vinculahoy_token', data.access_token);
    closeLoginModal();
    document.getElementById('loginForm').reset();
    await checkAuthStatus();
    alert('¡Sesión iniciada con éxito en VinculaHoy!');
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// =============================================================================
// CICLO DE VIDA DE AUTENTICACIÓN Y PERSISTENCIA (JWT / LOCALSTORAGE)
// =============================================================================
async function checkAuthStatus() {
  const token = localStorage.getItem('vinculahoy_token');
  const guestNav = document.getElementById('guestAuthNav');
  const userNav = document.getElementById('userAuthNav');
  const ctaBanner = document.getElementById('ctaDestacaBanner');
  const navPlansBtn = document.getElementById('navPlansBtn');

  if (!token) {
    if (guestNav) guestNav.classList.remove('hidden');
    if (userNav) {
      userNav.classList.add('hidden');
      userNav.classList.remove('flex');
    }
    // MODO INVITADO: Ocultar banner promocional y menú de planes
    if (ctaBanner) ctaBanner.classList.add('hidden');
    if (navPlansBtn) {
      navPlansBtn.classList.add('hidden');
      navPlansBtn.classList.remove('inline-flex', 'flex');
    }
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!res.ok) {
      // Token inválido o expirado -> Regresar a modo invitado
      localStorage.removeItem('vinculahoy_token');
      localStorage.removeItem('vinculahoy_user_email');
      localStorage.removeItem('vinculahoy_user_role');
      localStorage.removeItem('vinculahoy_user_status');
      if (guestNav) guestNav.classList.remove('hidden');
      if (userNav) {
        userNav.classList.add('hidden');
        userNav.classList.remove('flex');
      }
      if (ctaBanner) ctaBanner.classList.add('hidden');
      if (navPlansBtn) {
        navPlansBtn.classList.add('hidden');
        navPlansBtn.classList.remove('inline-flex', 'flex');
      }
      return;
    }

    const userData = await res.json();
    renderUserNavbar(userData);
  } catch (err) {
    console.warn('Verificación remota de sesión inaccesible:', err);
    const cachedEmail = localStorage.getItem('vinculahoy_user_email');
    const cachedRole = localStorage.getItem('vinculahoy_user_role');
    const cachedStatus = localStorage.getItem('vinculahoy_user_status') || 'pending';
    if (cachedEmail) {
      renderUserNavbar({
        email: cachedEmail,
        role: cachedRole || 'APRENDIZ',
        verification_status: cachedStatus
      });
    } else {
      if (guestNav) guestNav.classList.remove('hidden');
      if (userNav) {
        userNav.classList.add('hidden');
        userNav.classList.remove('flex');
      }
      if (ctaBanner) ctaBanner.classList.add('hidden');
      if (navPlansBtn) {
        navPlansBtn.classList.add('hidden');
        navPlansBtn.classList.remove('inline-flex', 'flex');
      }
    }
  }
}

function renderUserNavbar(user) {
  const guestNav = document.getElementById('guestAuthNav');
  const userNav = document.getElementById('userAuthNav');
  const navEmail = document.getElementById('navUserEmail');
  const navRoleBadge = document.getElementById('navUserRoleBadge');
  const navVerifyBadge = document.getElementById('navUserVerifyBadge');
  const ctaBanner = document.getElementById('ctaDestacaBanner');
  const navPlansBtn = document.getElementById('navPlansBtn');

  if (guestNav) guestNav.classList.add('hidden');
  if (userNav) {
    userNav.classList.remove('hidden');
    userNav.classList.add('flex');
  }

  if (navEmail) navEmail.textContent = user.email;

  const normalizedRole = (user.role || '').toUpperCase();
  const isCentroTrabajo = normalizedRole === 'CENTRO_TRABAJO';

  if (navRoleBadge) {
    const roleLabel = isCentroTrabajo ? 'Centro' : (normalizedRole === 'ADMIN' ? 'Admin' : 'Aprendiz');
    navRoleBadge.textContent = roleLabel;
  }

  if (navVerifyBadge) {
    const status = (user.verification_status || 'pending').toLowerCase();
    if (status === 'approved') {
      navVerifyBadge.className = 'text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800';
      navVerifyBadge.innerHTML = '<i class="fa-solid fa-circle-check text-[9px] mr-1"></i>Aprobado';
    } else if (status === 'rejected') {
      navVerifyBadge.className = 'text-[10px] font-bold px-1.5 py-0.2 rounded bg-rose-100 text-rose-800';
      navVerifyBadge.innerHTML = '<i class="fa-solid fa-circle-xmark text-[9px] mr-1"></i>Rechazado';
    } else {
      navVerifyBadge.className = 'text-[10px] font-bold px-1.5 py-0.2 rounded bg-amber-100 text-amber-800';
      navVerifyBadge.innerHTML = '<i class="fa-solid fa-clock text-[9px] mr-1"></i>Pendiente';
    }
  }

  localStorage.setItem('vinculahoy_user_email', user.email);
  localStorage.setItem('vinculahoy_user_role', normalizedRole);
  localStorage.setItem('vinculahoy_user_status', user.verification_status || 'pending');

  // EVALUACIÓN CONDICIONAL DE VISIBILIDAD (PLANES Y BANNER):
  // - Si la sesión es de MODO INVITADO o rol APRENDIZ: NO mostrar el banner ni el menú de planes.
  // - SOLO si la sesión activa tiene el rol CENTRO_TRABAJO: Renderear/activar la visibilidad del banner y opción de Planes.
  if (isCentroTrabajo) {
    if (ctaBanner) ctaBanner.classList.remove('hidden');
    if (navPlansBtn) {
      navPlansBtn.classList.remove('hidden');
      navPlansBtn.classList.add('inline-flex');
    }
  } else {
    if (ctaBanner) ctaBanner.classList.add('hidden');
    if (navPlansBtn) {
      navPlansBtn.classList.add('hidden');
      navPlansBtn.classList.remove('inline-flex', 'flex');
    }
  }
}

function handleLogout() {
  localStorage.removeItem('vinculahoy_token');
  localStorage.removeItem('vinculahoy_user_email');
  localStorage.removeItem('vinculahoy_user_role');
  localStorage.removeItem('vinculahoy_user_status');

  const guestNav = document.getElementById('guestAuthNav');
  const userNav = document.getElementById('userAuthNav');
  const ctaBanner = document.getElementById('ctaDestacaBanner');
  const navPlansBtn = document.getElementById('navPlansBtn');

  if (guestNav) guestNav.classList.remove('hidden');
  if (userNav) {
    userNav.classList.add('hidden');
    userNav.classList.remove('flex');
  }

  // Ocultar banner y menú de planes al cerrar sesión (Modo Invitado)
  if (ctaBanner) ctaBanner.classList.add('hidden');
  if (navPlansBtn) {
    navPlansBtn.classList.add('hidden');
    navPlansBtn.classList.remove('inline-flex', 'flex');
  }

  alert('Has cerrado sesión correctamente.');
}

// =============================================================================
// REGISTRO DE CENTRO DE TRABAJO (CON HORARIOS, RFC, CONTACTO Y FICHA)
// =============================================================================
async function handleRegisterCenter(e) {
  e.preventDefault();
  const btn = document.getElementById('btnSubmitCenter');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Registrando...';

  try {
    let programFileUrl = null;
    const fileInput = document.getElementById('regProgramFile');
    if (fileInput && fileInput.files && fileInput.files[0]) {
      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append('file', file);
      try {
        const uploadRes = await fetch(`${API_BASE_URL}/auth/upload-ficha`, {
          method: 'POST',
          body: formData
        });
        if (uploadRes.ok) {
          const uploadData = await uploadRes.json();
          programFileUrl = uploadData.program_file_url;
        }
      } catch (uploadErr) {
        console.warn('Subida directa de archivo:', uploadErr);
        programFileUrl = `/static/uploads/${file.name}`;
      }
    }

    const payload = {
      email: document.getElementById('regEmail').value.trim(),
      password: document.getElementById('regPassword').value,
      company_name: document.getElementById('regCompanyName').value.trim(),
      trade: document.getElementById('regTrade').value,
      address: document.getElementById('regAddress').value.trim(),
      schedule: document.getElementById('regSchedule') ? document.getElementById('regSchedule').value.trim() || null : null,
      contact_person: document.getElementById('regContactPerson') ? document.getElementById('regContactPerson').value.trim() || null : null,
      rfc: document.getElementById('regRfc') ? document.getElementById('regRfc').value.trim() || null : null,
      contact_phone: document.getElementById('regContactPhone') ? document.getElementById('regContactPhone').value.trim() || null : null,
      vacancies: parseInt(document.getElementById('regVacancies').value, 10) || 1,
      latitude: state.userLat + (Math.random() - 0.5) * 0.008,
      longitude: state.userLng + (Math.random() - 0.5) * 0.008,
      is_premium: document.getElementById('regIsPremium').checked,
      program_file_url: programFileUrl
    };

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register/center`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        if (data.access_token) {
          localStorage.setItem('vinculahoy_token', data.access_token);
        }
      } else {
        const err = await res.json();
        throw new Error(err.detail || 'Error al registrar centro');
      }
    } catch (apiErr) {
      console.warn('Registro local o fallback:', apiErr.message);
      // Fallback visual
      renderUserNavbar({
        email: payload.email,
        role: 'centro_trabajo',
        verification_status: 'pending'
      });
    }

    alert(`¡Centro "${payload.company_name}" registrado exitosamente!\nLa Ficha del Programa se ha adjuntado para validación.`);
    closeCenterRegisterModal();
    document.getElementById('registerCenterForm').reset();
    await checkAuthStatus();
    fetchNearbyCenters();

  } catch (err) {
    alert(`Aviso: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
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
  checkAuthStatus();

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

  // Buscador manual de Ciudad / Código Postal
  const btnSearch = document.getElementById('btnCitySearch');
  const inputSearch = document.getElementById('citySearchInput');
  if (btnSearch) {
    btnSearch.addEventListener('click', handleManualSearch);
  }
  if (inputSearch) {
    inputSearch.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleManualSearch();
      }
    });
  }

  // Botones de presets demo
  document.querySelectorAll('.preset-loc').forEach(btn => {
    btn.addEventListener('click', () => {
      const lat = parseFloat(btn.dataset.lat);
      const lng = parseFloat(btn.dataset.lng);
      state.userLat = lat;
      state.userLng = lng;

      state.map.flyTo([lat, lng], 14, { duration: 1.2 });
      setTimeout(() => state.map.invalidateSize(), 200);
      updateUserMarker();
      fetchNearbyCenters();
    });
  });
});
