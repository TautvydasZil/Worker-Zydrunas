<template>
  <div class="map-picker">
    <div class="search-row">
      <input
        v-model="query"
        type="text"
        placeholder="Ieškoti adreso…"
        @keydown.enter.prevent="geocode"
      />
      <button type="button" class="search-btn" :disabled="!query.trim()" @click="geocode">
        Ieškoti
      </button>
    </div>
    <div ref="mapEl" class="map-container"></div>
    <p v-if="modelValue" class="location-label">
      📍 {{ modelValue.address || `${modelValue.lat.toFixed(5)}, ${modelValue.lng.toFixed(5)}` }}
    </p>
    <p v-else class="location-hint">Spustelėkite žemėlapyje, kad pažymėtumėte vietą</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

const props = defineProps({
  modelValue: Object  // { lat, lng, address } or null
})
const emit = defineEmits(['update:modelValue'])

const mapEl = ref(null)
const query = ref('')
let map = null
let marker = null

// Fix Leaflet default icon paths broken by Vite bundling
const DefaultIcon = L.icon({ iconUrl, iconRetinaUrl, shadowUrl, iconSize: [25, 41], iconAnchor: [12, 41] })
L.Marker.prototype.options.icon = DefaultIcon

onMounted(() => {
  const center = props.modelValue
    ? [props.modelValue.lat, props.modelValue.lng]
    : [55.1736, 23.8953]  // Lithuania centre
  const zoom = props.modelValue ? 14 : 7

  map = L.map(mapEl.value).setView(center, zoom)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map)

  if (props.modelValue) {
    placeMarker(props.modelValue.lat, props.modelValue.lng)
  }

  map.on('click', async (e) => {
    const { lat, lng } = e.latlng
    placeMarker(lat, lng)
    const address = await reverseGeocode(lat, lng)
    emit('update:modelValue', { lat, lng, address })
  })
})

onUnmounted(() => {
  if (map) { map.remove(); map = null }
})

watch(() => props.modelValue, (val) => {
  if (!map || !val) return
  placeMarker(val.lat, val.lng)
  map.setView([val.lat, val.lng], Math.max(map.getZoom(), 12))
})

function placeMarker(lat, lng) {
  if (marker) {
    marker.setLatLng([lat, lng])
  } else {
    marker = L.marker([lat, lng], { draggable: true }).addTo(map)
    marker.on('dragend', async () => {
      const { lat, lng } = marker.getLatLng()
      const address = await reverseGeocode(lat, lng)
      emit('update:modelValue', { lat, lng, address })
    })
  }
}

async function reverseGeocode(lat, lng) {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`,
      { headers: { 'Accept-Language': 'lt' } }
    )
    const data = await res.json()
    return data.display_name ?? null
  } catch {
    return null
  }
}

async function geocode() {
  if (!query.value.trim()) return
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query.value)}&format=json&limit=1`,
      { headers: { 'Accept-Language': 'lt' } }
    )
    const data = await res.json()
    if (!data.length) return
    const { lat, lon, display_name } = data[0]
    const latF = parseFloat(lat)
    const lngF = parseFloat(lon)
    map.setView([latF, lngF], 15)
    placeMarker(latF, lngF)
    emit('update:modelValue', { lat: latF, lng: lngF, address: display_name })
  } catch {}
}
</script>

<style scoped>
.map-picker { display: flex; flex-direction: column; gap: 8px; }

.search-row { display: flex; gap: 8px; }

.search-row input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text-h);
  font-size: 14px;
}

.search-row input:focus {
  outline: 2px solid var(--accent);
  outline-offset: -1px;
  border-color: transparent;
}

.search-btn {
  padding: 8px 14px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.search-btn:disabled { opacity: 0.5; cursor: default; }

.map-container {
  height: 300px;
  border-radius: 8px;
  border: 1px solid var(--border);
  overflow: hidden;
  z-index: 0;
}

.location-label {
  font-size: 13px;
  color: var(--text-h);
  margin: 0;
  line-height: 1.4;
}

.location-hint {
  font-size: 13px;
  color: var(--text);
  margin: 0;
  font-style: italic;
}
</style>
