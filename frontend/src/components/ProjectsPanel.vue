<template>
  <ConfirmDialog ref="confirmDialog" />
  <div class="projects-panel">
    <div class="panel-header">
      <h2>Projektai</h2>
      <button v-if="!showForm" class="add-btn" @click="startCreate">+ Pridėti projektą</button>
    </div>

    <!-- Create / Edit form -->
    <div v-if="showForm" class="form-card">
      <h3>{{ editId ? 'Redaguoti projektą' : 'Naujas projektas' }}</h3>
      <form @submit.prevent="save">
        <div class="field">
          <label>Pavadinimas</label>
          <input v-model="form.name" type="text" required placeholder="Projekto pavadinimas" />
        </div>
        <div class="field">
          <label>Vieta žemėlapyje</label>
          <MapPicker v-model="form.location" />
        </div>
        <p v-if="formError" class="error">{{ formError }}</p>
        <div class="form-actions">
          <button type="submit" :disabled="saving">{{ saving ? 'Saugoma…' : (editId ? 'Išsaugoti' : 'Sukurti') }}</button>
          <button type="button" class="cancel-btn" @click="cancelForm">Atšaukti</button>
        </div>
      </form>
    </div>

    <!-- Project list -->
    <div v-if="loadingProjects" class="loading">Kraunama…</div>
    <div v-else>
      <p v-if="!projects.length && !showForm" class="empty">Projektų dar nėra.</p>

      <!-- Active projects -->
      <template v-if="activeProjects.length">
        <p class="section-label">Aktyvūs ({{ activeProjects.length }})</p>
        <ul class="project-list">
          <li v-for="p in activeProjects" :key="p.id" class="project-card">
            <div class="project-info">
              <span class="project-name">{{ p.name }}</span>
              <span v-if="p.address" class="project-address">📍 {{ p.address }}</span>
              <span v-else-if="p.latitude != null" class="project-address">
                📍 {{ p.latitude.toFixed(5) }}, {{ p.longitude.toFixed(5) }}
              </span>
            </div>
            <div class="project-actions">
              <button class="complete-btn" @click="toggleComplete(p)">✓ Užbaigti</button>
              <button class="edit-btn" @click="startEdit(p)">Redaguoti</button>
              <button class="delete-btn" @click="remove(p.id)">Ištrinti</button>
            </div>
          </li>
        </ul>
      </template>

      <!-- Completed projects -->
      <template v-if="completedProjects.length">
        <button class="toggle-completed-btn" @click="showCompleted = !showCompleted">
          {{ showCompleted ? '▲' : '▼' }} Užbaigti ({{ completedProjects.length }})
        </button>
        <ul v-if="showCompleted" class="project-list completed-list">
          <li v-for="p in completedProjects" :key="p.id" class="project-card completed">
            <div class="project-info">
              <span class="project-name">{{ p.name }}</span>
              <span v-if="p.address" class="project-address">📍 {{ p.address }}</span>
              <span v-else-if="p.latitude != null" class="project-address">
                📍 {{ p.latitude.toFixed(5) }}, {{ p.longitude.toFixed(5) }}
              </span>
            </div>
            <div class="project-actions">
              <button class="reopen-btn" @click="toggleComplete(p)">↩ Atnaujinti</button>
              <button class="delete-btn" @click="remove(p.id)">Ištrinti</button>
            </div>
          </li>
        </ul>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MapPicker from './MapPicker.vue'
import API from '../api'
import ConfirmDialog from './ConfirmDialog.vue'

const confirmDialog = ref(null)

const projects = ref([])
const loadingProjects = ref(true)
const showForm = ref(false)
const showCompleted = ref(false)
const editId = ref(null)
const saving = ref(false)
const formError = ref('')

const activeProjects    = computed(() => projects.value.filter(p => !p.is_completed))
const completedProjects = computed(() => projects.value.filter(p => p.is_completed))

const emptyForm = () => ({ name: '', location: null })
const form = ref(emptyForm())

async function loadProjects() {
  loadingProjects.value = true
  const res = await API.get('/projects')
  projects.value = res.data
  loadingProjects.value = false
}

function startCreate() {
  editId.value = null
  form.value = emptyForm()
  formError.value = ''
  showForm.value = true
}

function startEdit(p) {
  editId.value = p.id
  form.value = {
    name: p.name,
    location: p.latitude != null
      ? { lat: p.latitude, lng: p.longitude, address: p.address }
      : null
  }
  formError.value = ''
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  editId.value = null
  form.value = emptyForm()
}

async function save() {
  formError.value = ''
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      latitude: form.value.location?.lat ?? null,
      longitude: form.value.location?.lng ?? null,
      address: form.value.location?.address ?? null
    }
    if (editId.value) {
      await API.put(`/projects/${editId.value}`, payload)
    } else {
      await API.post('/projects', payload)
    }
    cancelForm()
    await loadProjects()
  } catch (e) {
    formError.value = e.response?.data?.error || 'Nepavyko išsaugoti'
  } finally {
    saving.value = false
  }
}

async function toggleComplete(p) {
  await API.patch(`/projects/${p.id}/complete`)
  await loadProjects()
}

async function remove(id) {
  const ok = await confirmDialog.value.show('Ar tikrai norite ištrinti šį projektą?')
  if (!ok) return
  await API.delete(`/projects/${id}`)
  await loadProjects()
}

onMounted(loadProjects)
</script>

<style scoped>
.projects-panel { display: flex; flex-direction: column; gap: 18px; }

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header h2 { margin: 0; }

.add-btn {
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
  transition: background 0.15s;
}

.add-btn:hover { background: var(--accent-hover); }

.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  box-shadow: var(--shadow-sm);
}

h3 { margin: 0 0 16px; font-size: 15px; }

form { display: flex; flex-direction: column; gap: 14px; }

.field { display: flex; flex-direction: column; gap: 6px; }

label { font-size: 13px; font-weight: 500; color: var(--text-h); }

input {
  padding: 9px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.form-actions { display: flex; gap: 10px; }

button[type="submit"] {
  padding: 10px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

button[type="submit"]:hover { background: var(--accent-hover); }
button:disabled { opacity: 0.55; cursor: default; }

.cancel-btn {
  padding: 10px 16px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.cancel-btn:hover { border-color: var(--text-h); color: var(--text-h); }

.loading { color: var(--text); padding: 32px 0; text-align: center; font-size: 14px; }

.empty { color: var(--text); font-size: 13px; margin: 0; }

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text);
  margin: 0 0 8px;
}

.toggle-completed-btn {
  margin: 16px 0 8px;
  padding: 0;
  background: none;
  border: none;
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.toggle-completed-btn:hover { color: var(--text-h); }

.project-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.completed-list { margin-top: 4px; }

.project-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
  transition: border-color 0.15s;
}

.project-card:hover { border-color: var(--accent-border); }

.project-card.completed {
  opacity: 0.6;
}

.project-card.completed .project-name {
  text-decoration: line-through;
  color: var(--text);
}

.project-info { display: flex; flex-direction: column; gap: 3px; flex: 1; }

.project-name { font-size: 14px; font-weight: 600; color: var(--text-h); }

.project-address { font-size: 12px; color: var(--text); }

.project-actions { display: flex; gap: 8px; flex-shrink: 0; }

.edit-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.edit-btn:hover { border-color: var(--accent); color: var(--accent); }

.complete-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid #16a34a;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: #16a34a;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.complete-btn:hover { background: #16a34a; color: #fff; }

.reopen-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.reopen-btn:hover { border-color: var(--accent); color: var(--accent); }

.delete-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.delete-btn:hover { border-color: var(--danger); color: var(--danger); }

.error { color: var(--danger); font-size: 13px; margin: 0; }
</style>
