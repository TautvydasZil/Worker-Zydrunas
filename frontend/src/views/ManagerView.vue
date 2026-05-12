<template>
  <ConfirmDialog ref="confirmDialog" />
  <DateRangePicker ref="dateRangePicker" />
  <div class="dashboard">
    <header class="topbar">
      <ThemeToggle />
      <router-link to="/" class="back-link">Mano duomenys</router-link>
      <button class="app-name" @click="activeTab = 'home'">Darbuotojų Apskaita — Valdymas</button>
      <div class="user-area">
        <span class="username">{{ user?.first_name }} {{ user?.last_name }}</span>
        <button class="logout-btn" @click="logout">Atsijungti</button>
      </div>
    </header>

    <main class="content">

      <!-- ── Home ── -->
      <template v-if="activeTab === 'home'">
        <div class="quick-nav">
          <button class="quick-card" @click="activeTab = 'stats'">
            <span class="qc-icon">📊</span>
            <span class="qc-label">Statistika</span>
            <span class="qc-sub">Darbuotojų valandos ir prašymai</span>
          </button>
          <button class="quick-card" @click="activeTab = 'requests'">
            <span class="qc-icon">📋</span>
            <span class="qc-label">Prašymai</span>
            <span class="qc-sub">Atostogos ir nedarbingumas</span>
            <span v-if="pendingCount" class="qc-badge">{{ pendingCount }}</span>
          </button>
          <button class="quick-card" @click="activeTab = 'projects'">
            <span class="qc-icon">📌</span>
            <span class="qc-label">Projektai</span>
            <span class="qc-sub">Tvarkyti projektų sąrašą</span>
          </button>
          <button class="quick-card" @click="activeTab = 'invites'">
            <span class="qc-icon">✉️</span>
            <span class="qc-label">Pakvietimai</span>
            <span class="qc-sub">Pakviesti naujus darbuotojus</span>
          </button>
          <button class="quick-card" @click="activeTab = 'employees'">
            <span class="qc-icon">👥</span>
            <span class="qc-label">Darbuotojai</span>
            <span class="qc-sub">Tvarkyti darbuotojų paskyras</span>
          </button>
        </div>
      </template>

      <!-- ── Statistika: pasirinkimas ── -->
      <template v-else-if="activeTab === 'stats' && statsStep === 'pick'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <h2>Darbuotojų statistika</h2>
        <div class="search-box">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 3a6 6 0 100 12A6 6 0 009 3zM1 9a8 8 0 1114.32 4.906l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387A8 8 0 011 9z" clip-rule="evenodd" /></svg>
          <input v-model="statsSearch" type="text" placeholder="Ieškoti darbuotojo…" />
        </div>
        <div v-if="loading" class="loading">Kraunama…</div>
        <ul v-else class="picker-list">
          <li>
            <button class="picker-card all-card" @click="selectStatsUser(null)">
              <span class="picker-icon">👥</span>
              <span class="picker-name">Visi darbuotojai</span>
              <span class="picker-sub">Bendra statistika</span>
            </button>
          </li>
          <li v-for="u in filteredStatsUsers" :key="u.id">
            <button class="picker-card" @click="selectStatsUser(u.id)">
              <span class="picker-avatar">{{ u.first_name[0] }}{{ u.last_name[0] }}</span>
              <span class="picker-name">{{ u.first_name }} {{ u.last_name }}</span>
              <span class="picker-sub">{{ roleLabel(u.role) }} · {{ u.is_active ? 'Aktyvus' : 'Atleistas' }}</span>
            </button>
          </li>
          <li v-if="!filteredStatsUsers.length && statsSearch">
            <p class="empty">Nerasta: „{{ statsSearch }}"</p>
          </li>
        </ul>
      </template>

      <!-- ── Statistika: rodinys ── -->
      <template v-else-if="activeTab === 'stats' && statsStep === 'view'">
        <div class="stats-topbar">
          <button class="back-btn" @click="statsStep = 'pick'">← Pasirinkimas</button>
          <h2 class="stats-title">
            {{ selectedUserId ? displayName(selectedUserId) : 'Visi darbuotojai' }}
          </h2>
          <div class="stats-date-row">
            <button type="button" class="date-btn" @click="pickStatsRange">
              <svg class="date-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" /></svg>
              {{ statsFrom && statsTo ? formatDate(statsFrom) + ' — ' + formatDate(statsTo) : 'Pasirinkti laikotarpį…' }}
            </button>
            <button v-if="statsFrom || statsTo" class="clear-btn" @click="clearStatsFilter">Išvalyti</button>
            <button v-if="hours.length || approvedLeave.length" class="pdf-btn" @click="downloadPdf">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" style="width:14px;height:14px;flex-shrink:0"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
              PDF
            </button>
          </div>
        </div>

        <div v-if="statsLoading" class="loading">Kraunama…</div>
        <div v-else>
          <div class="summary-cards">
            <div class="card">
              <div class="card-value">{{ totalHours.toFixed(1) }}</div>
              <div class="card-label">Iš viso valandų</div>
            </div>
            <div class="card">
              <div class="card-value">{{ approvedVacationDays }}</div>
              <div class="card-label">Atostogų dienos</div>
            </div>
            <div class="card">
              <div class="card-value">{{ approvedSickDays }}</div>
              <div class="card-label">Nedarbingumo dienos</div>
            </div>
          </div>

          <div class="section">
            <h3>Darbo valandos</h3>
            <p v-if="!hours.length" class="empty">Įrašų nėra.</p>
            <div v-else class="table-wrap">
              <table>
                <thead><tr><th>Darbuotojas</th><th>Data</th><th>Valandos</th><th>Pastabos</th></tr></thead>
                <tbody>
                  <tr v-for="e in hours" :key="e.id">
                    <td>{{ displayName(e.user_id) }}</td>
                    <td>{{ e.date }}</td>
                    <td>{{ e.hours }}</td>
                    <td>{{ e.notes }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="section">
            <h3>Patvirtinti prašymai</h3>
            <p v-if="!approvedLeave.length" class="empty">Patvirtintų prašymų nėra.</p>
            <div v-else class="table-wrap">
              <table>
                <thead><tr><th>Darbuotojas</th><th>Tipas</th><th>Nuo</th><th>Iki</th><th>Dienų</th><th>Pastabos</th></tr></thead>
                <tbody>
                  <tr v-for="r in approvedLeave" :key="r.id">
                    <td>{{ displayName(r.user_id) }}</td>
                    <td>
                      <span :class="['type-badge', r.type]">
                        {{ r.type === 'vacation' ? 'Atostogos' : 'Nedarbingumas' }}
                      </span>
                    </td>
                    <td>{{ r.start_date }}</td>
                    <td>{{ r.end_date }}</td>
                    <td>{{ r.days }}</td>
                    <td>{{ r.notes }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </template>

      <!-- ── Prašymai ── -->
      <template v-else-if="activeTab === 'requests'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <h2>Darbuotojų prašymai</h2>
        <div class="filter-row">
          <label>Rodyti:</label>
          <select v-model="requestFilter" @change="loadRequests">
            <option value="">Visi</option>
            <option value="pending">Laukiantys</option>
            <option value="approved">Patvirtinti</option>
            <option value="denied">Atmesti</option>
          </select>
          <label style="margin-left:12px">Darbuotojas:</label>
          <select v-model="requestUserId" @change="loadRequests">
            <option :value="null">Visi</option>
            <option v-for="u in nonAdminUsers" :key="u.id" :value="u.id">
              {{ u.first_name }} {{ u.last_name }}
            </option>
          </select>
        </div>
        <div v-if="requestsLoading" class="loading">Kraunama…</div>
        <div v-else>
          <p v-if="!leaveRequests.length" class="empty">Prašymų nėra.</p>
          <ul v-else class="request-list">
            <li v-for="req in leaveRequests" :key="req.id" class="request-card">
              <div class="req-info">
                <span class="req-worker">{{ displayName(req.user_id) }}</span>
                <span :class="['type-badge', req.type]">
                  {{ req.type === 'vacation' ? 'Atostogos' : 'Nedarbingumas' }}
                </span>
                <span class="req-dates">{{ req.start_date }} — {{ req.end_date }}</span>
                <span class="req-days">{{ req.days }} d.</span>
                <span v-if="req.notes" class="req-notes">{{ req.notes }}</span>
              </div>
              <div class="req-actions">
                <span v-if="req.status !== 'pending'" :class="['status-badge', req.status]">
                  {{ statusLabel(req.status) }}
                </span>
                <template v-if="req.status === 'pending'">
                  <button class="approve-btn" @click="review(req.id, 'approved')">Patvirtinti</button>
                  <button class="deny-btn" @click="review(req.id, 'denied')">Atmesti</button>
                </template>
              </div>
            </li>
          </ul>
        </div>
      </template>

      <!-- ── Projektai ── -->
      <template v-else-if="activeTab === 'projects'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <ProjectsPanel />
      </template>

      <!-- ── Darbuotojai ── -->
      <template v-else-if="activeTab === 'employees'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <h2>Darbuotojai</h2>
        <div class="search-box" style="margin-bottom:16px">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 3a6 6 0 100 12A6 6 0 009 3zM1 9a8 8 0 1114.32 4.906l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387A8 8 0 011 9z" clip-rule="evenodd" /></svg>
          <input v-model="employeeSearch" type="text" placeholder="Ieškoti pagal vardą…" />
        </div>
        <p v-if="!filteredEmployees.length" class="empty">{{ employeeSearch ? `Nerasta: „${employeeSearch}"` : 'Darbuotojų dar nėra.' }}</p>
        <ul v-else class="employee-list">
          <li v-for="u in filteredEmployees" :key="u.id" class="employee-card">
            <div class="emp-info">
              <span class="emp-name">{{ u.first_name }} {{ u.last_name }}</span>
              <span class="emp-role">{{ roleLabel(u.role) }}</span>
              <span :class="['emp-status', u.is_active ? 'active' : 'inactive']">
                {{ u.is_active ? 'Aktyvus' : 'Atleistas' }}
              </span>
            </div>
            <div class="emp-actions">
              <button v-if="u.is_active" class="dismiss-btn" @click="dismissUser(u.id)">Atleisti</button>
              <button v-else class="reactivate-btn" @click="reactivateUser(u.id)">Atnaujinti</button>
            </div>
          </li>
        </ul>
      </template>

      <!-- ── Pakvietimai ── -->
      <template v-else-if="activeTab === 'invites'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <h2>Pakviesti vartotoją</h2>
        <div class="form-card">
          <form @submit.prevent="createInvite">
            <div class="invite-row">
              <div class="field">
                <label>El. paštas (informaciniam)</label>
                <input v-model="inviteEmail" type="email" placeholder="darbuotojas@imone.lt" required />
              </div>
              <div class="field field-role">
                <label>Vaidmuo</label>
                <select v-model="inviteRole">
                  <option value="worker">Darbuotojas</option>
                  <option value="manager">Vadybininkas</option>
                </select>
              </div>
              <button type="submit" :disabled="inviteLoading">
                {{ inviteLoading ? 'Generuojama…' : 'Generuoti nuorodą' }}
              </button>
            </div>
            <p v-if="inviteError" class="error">{{ inviteError }}</p>
          </form>
          <div v-if="newLinkEmail" class="new-link-box">
            <p class="new-link-label">✓ Pakvietimas išsiųstas {{ newLinkEmail }}</p>
            <p class="link-note">Galioja 7 dienas. Vienkartinis naudojimas.</p>
          </div>
        </div>

        <h2>Laukiantys pakvietimai</h2>
        <div v-if="invitesLoading" class="loading">Kraunama…</div>
        <div v-else>
          <p v-if="!invites.length" class="empty">Pakvietimų dar nėra.</p>
          <div v-else class="table-wrap">
            <table>
              <thead><tr><th>El. paštas</th><th>Vaidmuo</th><th>Būsena</th><th>Galioja iki</th><th></th></tr></thead>
              <tbody>
                <tr v-for="inv in invites" :key="inv.id">
                  <td>{{ inv.email }}</td>
                  <td>{{ roleLabel(inv.role) }}</td>
                  <td>
                    <span :class="['status-badge', inv.used ? 'approved' : isExpired(inv) ? 'denied' : 'pending']">
                      {{ inv.used ? 'Panaudota' : isExpired(inv) ? 'Pasibaigė' : 'Laukiama' }}
                    </span>
                  </td>
                  <td>{{ inv.expires_at.slice(0, 10) }}</td>
                  <td><button class="deny-btn" @click="revokeInvite(inv.id)">Atšaukti</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'
import API from '../api'
import ProjectsPanel from '../components/ProjectsPanel.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import DateRangePicker from '../components/DateRangePicker.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

const confirmDialog    = ref(null)
const dateRangePicker  = ref(null)

const monthNames = ['sausio','vasario','kovo','balandžio','gegužės','birželio','liepos','rugpjūčio','rugsėjo','spalio','lapkričio','gruodžio']
function formatDate(str) {
  if (!str) return '—'
  const d = new Date(str + 'T00:00:00')
  return `${d.getDate()} ${monthNames[d.getMonth()]} ${d.getFullYear()}`
}
async function pickStatsRange() {
  const result = await dateRangePicker.value.show(statsFrom.value, statsTo.value, 'Laikotarpis')
  if (result === null) return
  statsFrom.value = result.from
  statsTo.value   = result.to
  statsLoading.value = true
  await loadStats()
  statsLoading.value = false
}

const { user, fetchMe, logout } = useAuth()

const activeTab = ref('home')

// ── Users lookup ──
const users = ref([])
const nonAdminUsers = computed(() => users.value.filter(u => u.role !== 'admin'))
function displayName(id) {
  const u = users.value.find(u => u.id === id)
  return u ? `${u.first_name} ${u.last_name}` : `#${id}`
}
const roleLabels = { worker: 'Darbuotojas', manager: 'Vadybininkas', admin: 'Administratorius' }
const roleLabel = (r) => roleLabels[r] ?? r

// ── Statistika ──
const hours = ref([])
const allLeave = ref([])
const selectedUserId = ref(null)
const statsFrom = ref('')
const statsTo = ref('')
const loading = ref(true)
const statsLoading = ref(false)
const statsStep = ref('pick')
const statsSearch = ref('')

const filteredStatsUsers = computed(() => {
  const q = statsSearch.value.trim().toLowerCase()
  if (!q) return nonAdminUsers.value
  return nonAdminUsers.value.filter(u =>
    `${u.first_name} ${u.last_name}`.toLowerCase().includes(q)
  )
})

async function selectStatsUser(userId) {
  selectedUserId.value = userId
  statsFrom.value = ''
  statsTo.value = ''
  statsStep.value = 'view'
  statsLoading.value = true
  await loadStats()
  statsLoading.value = false
}

const totalHours = computed(() => hours.value.reduce((sum, e) => sum + e.hours, 0))
const approvedLeave = computed(() => allLeave.value.filter(r => r.status === 'approved'))
const approvedVacationDays = computed(() =>
  approvedLeave.value.filter(r => r.type === 'vacation').reduce((s, r) => s + r.days, 0)
)
const approvedSickDays = computed(() =>
  approvedLeave.value.filter(r => r.type === 'sick').reduce((s, r) => s + r.days, 0)
)

async function loadStats() {
  const params = {}
  if (selectedUserId.value) params.user_id = selectedUserId.value
  if (statsFrom.value) params.date_from = statsFrom.value
  if (statsTo.value) params.date_to = statsTo.value
  const [h, l] = await Promise.all([
    API.get('/hours', { params }),
    API.get('/leave', { params })
  ])
  hours.value = h.data
  allLeave.value = l.data
}

async function clearStatsFilter() {
  statsFrom.value = ''
  statsTo.value = ''
  statsLoading.value = true
  await loadStats()
  statsLoading.value = false
}

function lt(str) {
  return String(str)
    .replace(/ą/g,'a').replace(/č/g,'c').replace(/ę/g,'e').replace(/ė/g,'e')
    .replace(/į/g,'i').replace(/š/g,'s').replace(/ų/g,'u').replace(/ū/g,'u').replace(/ž/g,'z')
    .replace(/Ą/g,'A').replace(/Č/g,'C').replace(/Ę/g,'E').replace(/Ė/g,'E')
    .replace(/Į/g,'I').replace(/Š/g,'S').replace(/Ų/g,'U').replace(/Ū/g,'U').replace(/Ž/g,'Z')
}

function downloadPdf() {
  const doc = new jsPDF()
  const workerName = lt(selectedUserId.value ? displayName(selectedUserId.value) : 'Visi darbuotojai')
  const period = statsFrom.value && statsTo.value
    ? `${statsFrom.value} - ${statsTo.value}`
    : 'Visas laikotarpis'

  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.text('Darbo valandu ataskaita', 14, 18)

  doc.setFontSize(11)
  doc.setFont('helvetica', 'normal')
  doc.text(`Darbuotojas: ${workerName}`, 14, 28)
  doc.text(`Laikotarpis: ${period}`, 14, 35)

  autoTable(doc, {
    startY: 42,
    head: [['Viso valandu', 'Atostogu dienos', 'Nedarbingumo dienos']],
    body: [[totalHours.value.toFixed(1), approvedVacationDays.value, approvedSickDays.value]],
    styles: { fontSize: 10, halign: 'center' },
    headStyles: { fillColor: [79, 70, 229], halign: 'center' },
    theme: 'grid',
  })

  let y = doc.lastAutoTable.finalY + 10

  if (hours.value.length) {
    const workerTotals = {}
    hours.value.forEach(e => {
      const name = lt(displayName(e.user_id))
      workerTotals[name] = (workerTotals[name] || 0) + e.hours
    })
    const summaryRows = Object.entries(workerTotals).map(([name, h]) => [name, h.toFixed(1)])

    if (summaryRows.length > 1) {
      doc.setFontSize(12)
      doc.setFont('helvetica', 'bold')
      doc.text('Valandu suvestine', 14, y)
      y += 4

      autoTable(doc, {
        startY: y,
        head: [['Darbuotojas', 'Viso valandu']],
        body: summaryRows,
        styles: { fontSize: 9 },
        headStyles: { fillColor: [79, 70, 229] },
        alternateRowStyles: { fillColor: [245, 247, 255] },
      })
      y = doc.lastAutoTable.finalY + 10
    }

    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.text('Darbo valandos', 14, y)
    y += 4

    autoTable(doc, {
      startY: y,
      head: [['Darbuotojas', 'Data', 'Pradzia', 'Pabaiga', 'Valandos', 'Pastabos']],
      body: hours.value.map(e => [
        lt(displayName(e.user_id)),
        e.date,
        e.start_time ?? '-',
        e.end_time ?? '-',
        e.hours,
        lt(e.notes ?? '')
      ]),
      styles: { fontSize: 9 },
      headStyles: { fillColor: [79, 70, 229] },
      alternateRowStyles: { fillColor: [245, 247, 255] },
    })
    y = doc.lastAutoTable.finalY + 10
  }

  if (approvedLeave.value.length) {
    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.text('Patvirtinti prasymai', 14, y)
    y += 4

    autoTable(doc, {
      startY: y,
      head: [['Darbuotojas', 'Tipas', 'Nuo', 'Iki', 'Dienu', 'Pastabos']],
      body: approvedLeave.value.map(r => [
        lt(displayName(r.user_id)),
        r.type === 'vacation' ? 'Atostogos' : 'Nedarbingumas',
        r.start_date,
        r.end_date,
        r.days,
        lt(r.notes ?? '')
      ]),
      styles: { fontSize: 9 },
      headStyles: { fillColor: [79, 70, 229] },
      alternateRowStyles: { fillColor: [245, 247, 255] },
    })
  }

  const safeName = workerName.replace(/\s+/g, '_')
  doc.save(`ataskaita_${safeName}_${statsFrom.value || 'visi'}.pdf`)
}

// ── Prašymai ──
const leaveRequests = ref([])
const requestFilter = ref('')
const requestUserId = ref(null)
const requestsLoading = ref(false)
const pendingCount = computed(() => leaveRequests.value.filter(r => r.status === 'pending').length)

function statusLabel(s) {
  return { pending: 'Laukiama', approved: 'Patvirtinta', denied: 'Atmesta' }[s] ?? s
}

async function loadRequests() {
  requestsLoading.value = true
  const params = {}
  if (requestFilter.value) params.status = requestFilter.value
  if (requestUserId.value) params.user_id = requestUserId.value
  const res = await API.get('/leave', { params })
  leaveRequests.value = res.data
  requestsLoading.value = false
}

async function review(id, status) {
  await API.patch(`/leave/${id}/review`, { status })
  await Promise.all([loadRequests(), loadStats()])
}

// ── Darbuotojai ──
const employeeSearch = ref('')
const filteredEmployees = computed(() => {
  const q = employeeSearch.value.trim().toLowerCase()
  if (!q) return nonAdminUsers.value
  return nonAdminUsers.value.filter(u =>
    `${u.first_name} ${u.last_name}`.toLowerCase().includes(q)
  )
})

async function dismissUser(id) {
  const ok = await confirmDialog.value.show('Ar tikrai norite atleisti šį darbuotoją? Jis nebegalės prisijungti.')
  if (!ok) return
  await API.patch(`/users/${id}/dismiss`)
  const res = await API.get('/users')
  users.value = res.data
}

async function reactivateUser(id) {
  await API.patch(`/users/${id}/reactivate`)
  const res = await API.get('/users')
  users.value = res.data
}

// ── Pakvietimai ──
const invites = ref([])
const invitesLoading = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('worker')
const inviteLoading = ref(false)
const inviteError = ref('')
const newLink = ref('')
const newLinkEmail = ref('')
const copied = ref(false)

function isExpired(inv) { return new Date(inv.expires_at) < new Date() }

async function loadInvites() {
  invitesLoading.value = true
  const res = await API.get('/invites')
  invites.value = res.data
  invitesLoading.value = false
}

async function createInvite() {
  inviteError.value = ''
  inviteLoading.value = true
  newLink.value = ''
  copied.value = false
  try {
    const res = await API.post('/invites', { email: inviteEmail.value, role: inviteRole.value })
    newLink.value = `${window.location.origin}/register?token=${res.data.token}`
    newLinkEmail.value = inviteEmail.value
    inviteEmail.value = ''
    inviteRole.value = 'worker'
    await loadInvites()
  } catch (e) {
    inviteError.value = e.response?.data?.error || 'Nepavyko sukurti pakvietimo'
  } finally {
    inviteLoading.value = false
  }
}

async function revokeInvite(id) {
  const ok = await confirmDialog.value.show('Ar tikrai norite atšaukti šį pakvietimą?')
  if (!ok) return
  await API.delete(`/invites/${id}`)
  await loadInvites()
}

async function copyLink() {
  await navigator.clipboard.writeText(newLink.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

onMounted(async () => {
  loading.value = true
  await fetchMe()
  const res = await API.get('/users')
  users.value = res.data
  await Promise.all([loadRequests(), loadInvites()])
  loading.value = false
})
</script>

<style scoped>
.dashboard { min-height: 100svh; display: flex; flex-direction: column; background: var(--bg); }

/* ── Topbar ── */
.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px clamp(16px, 4vw, 28px);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  min-height: 52px;
  height: auto;
  flex-shrink: 0;
  flex-wrap: wrap;
  box-shadow: var(--shadow-sm);
}

.app-name {
  font-weight: 700;
  font-size: 15px;
  color: var(--text-h);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  flex: 1;
  min-width: 0;
  font-family: inherit;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-name:hover { color: var(--accent); }

.user-area { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.username { font-size: 13px; color: var(--text); font-weight: 500; display: none; }

@media (min-width: 480px) {
  .username { display: inline; }
}

.back-link {
  font-size: 13px;
  font-weight: 500;
  color: var(--accent);
  text-decoration: none;
  padding: 5px 12px;
  border: 1.5px solid var(--accent-border);
  border-radius: var(--radius-sm);
  background: var(--accent-bg);
  transition: background 0.15s;
}

.back-link:hover { background: var(--accent); color: #fff; }

.logout-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.logout-btn:hover { border-color: var(--danger); color: var(--danger); }

/* ── Content ── */
.content {
  padding: clamp(16px, 4vw, 28px);
  width: 100%;
  box-sizing: border-box;
}

h2 { margin: 0 0 18px; }
h3 { margin: 0 0 14px; font-size: 15px; }

.loading { color: var(--text); padding: 32px 0; text-align: center; font-size: 14px; }

/* ── Nav cards ── */
.quick-nav {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.quick-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 20px 22px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.1s;
}

.quick-card:hover {
  border-color: var(--accent-border);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.qc-icon { font-size: 22px; margin-bottom: 8px; }
.qc-label { font-size: 15px; font-weight: 600; color: var(--text-h); }
.qc-sub { font-size: 12px; color: var(--text); }

.qc-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  background: var(--accent);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
}

/* ── Back button ── */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
  padding: 7px 14px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: color 0.15s, border-color 0.15s;
}

.back-btn:hover { color: var(--text-h); border-color: var(--text-h); }

/* ── Filters ── */
.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 22px;
  flex-wrap: wrap;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

select {
  padding: 7px 10px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 13px;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.date-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 11px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.date-btn:hover { border-color: var(--accent-border); background: var(--accent-bg); }
.date-btn:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-ring); }
.date-icon { width: 14px; height: 14px; color: var(--text); flex-shrink: 0; }

label { font-size: 13px; font-weight: 500; color: var(--text-h); }

.clear-btn {
  padding: 7px 13px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.clear-btn:hover { border-color: var(--text-h); color: var(--text-h); }

.pdf-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 13px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
  transition: background 0.15s;
}

.pdf-btn:hover { background: var(--accent-hover); }

/* ── Summary cards ── */
.summary-cards { display: flex; gap: 14px; margin-bottom: 24px; flex-wrap: wrap; }

.card {
  flex: 1;
  min-width: 100px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: clamp(12px, 2.5vw, 20px) clamp(14px, 3vw, 22px);
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.card-value { font-size: clamp(24px, 7vw, 34px); font-weight: 700; color: var(--accent); letter-spacing: -0.02em; }
.card-label { font-size: 11px; color: var(--text); margin-top: 5px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }

.section { margin-bottom: 28px; }

/* ── Tables ── */
table { width: 100%; border-collapse: collapse; font-size: 13px; }

thead tr {
  background: var(--muted);
  border-bottom: 2px solid var(--border);
}

th {
  text-align: left;
  padding: 10px 14px;
  color: var(--text);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  text-align: left;
  padding: 10px 14px;
  color: var(--text-h);
  border-bottom: 1px solid var(--border);
}

tbody tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: var(--muted); }

.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
  box-shadow: var(--shadow-sm);
}

table { min-width: 480px; }

.empty { color: var(--text); font-size: 13px; padding: 16px 0; margin: 0; }

/* ── Requests ── */
.request-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }

.request-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
}

.req-info { display: flex; align-items: center; gap: 10px; flex: 1; flex-wrap: wrap; }
.req-worker { font-size: 14px; font-weight: 600; color: var(--text-h); }
.req-dates { font-size: 13px; color: var(--text-h); }
.req-days { font-size: 12px; color: var(--text); font-weight: 500; }
.req-notes { font-size: 12px; color: var(--text); font-style: italic; }
.req-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.type-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 99px;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.type-badge.vacation { background: #dbeafe; color: #1d4ed8; }
.type-badge.sick     { background: #fef9c3; color: #92400e; }

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 99px;
  white-space: nowrap;
}
.status-badge.pending  { background: var(--accent-bg); color: var(--accent); }
.status-badge.approved { background: #dcfce7; color: #166534; }
.status-badge.denied   { background: var(--danger-bg); color: #991b1b; }

.approve-btn {
  padding: 6px 14px;
  background: #22c55e;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.approve-btn:hover { background: #16a34a; }

.deny-btn {
  padding: 6px 14px;
  background: transparent;
  color: var(--danger);
  border: 1.5px solid var(--danger);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.deny-btn:hover { background: var(--danger-bg); }

/* ── Invites ── */
.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: clamp(14px, 3vw, 22px) clamp(16px, 4vw, 24px);
  margin-bottom: 28px;
  box-shadow: var(--shadow-sm);
}

.invite-row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.field { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 140px; }
.field-role { flex: 1; min-width: 130px; }

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

input:focus, select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

button[type="submit"] {
  padding: 9px 18px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  align-self: stretch;
  width: 100%;
  font-family: inherit;
  transition: background 0.15s;
}

button[type="submit"]:hover { background: var(--accent-hover); }
button:disabled { opacity: 0.55; cursor: default; }

@media (min-width: 640px) {
  button[type="submit"] { width: auto; align-self: flex-end; }
}

.new-link-box {
  margin-top: 16px;
  padding: 14px 16px;
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  border-radius: var(--radius-sm);
}

.new-link-label { font-size: 13px; color: var(--text-h); font-weight: 500; margin: 0 0 8px; }
.link-row { display: flex; align-items: center; gap: 10px; }

.link-text {
  flex: 1;
  font-size: 12px;
  word-break: break-all;
  white-space: normal;
  background: var(--surface);
  padding: 7px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-h);
  display: block;
  border: 1px solid var(--accent-border);
}

.copy-btn {
  padding: 7px 14px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  font-family: inherit;
  transition: background 0.15s;
}

.copy-btn:hover { background: var(--accent-hover); }

.link-note { font-size: 12px; color: var(--text); margin: 8px 0 0; }
.error { color: var(--danger); font-size: 13px; margin: 8px 0 0; }

/* ── Search box ── */
.search-box {
  position: relative;
  margin-bottom: 16px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text);
  pointer-events: none;
}

.search-box input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px 10px 36px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.search-box input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

/* ── Stats picker ── */
.picker-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-card {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.1s;
}

.picker-card:hover {
  border-color: var(--accent-border);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.all-card { border-color: var(--accent-border); background: var(--accent-bg); }

.picker-icon { font-size: 22px; flex-shrink: 0; }

.picker-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  text-transform: uppercase;
}

.picker-name { font-size: 15px; font-weight: 600; color: var(--text-h); flex: 1; }
.picker-sub { font-size: 12px; color: var(--text); }

/* ── Stats view topbar ── */
.stats-topbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
  flex-wrap: wrap;
}

.stats-title { margin: 0; flex: 1; font-size: 18px; }

.stats-date-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.date-sep { color: var(--text); font-size: 13px; }

/* ── Employees ── */
.employee-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }

.employee-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

.emp-info { display: flex; align-items: center; gap: 10px; flex: 1; flex-wrap: wrap; }
.emp-name { font-size: 14px; font-weight: 600; color: var(--text-h); }

.emp-role {
  font-size: 11px;
  font-weight: 500;
  color: var(--text);
  background: var(--muted);
  padding: 3px 9px;
  border-radius: 99px;
  border: 1px solid var(--border);
}

.emp-status { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 99px; }
.emp-status.active   { background: #dcfce7; color: #166534; }
.emp-status.inactive { background: var(--danger-bg); color: #991b1b; }

.emp-actions { flex-shrink: 0; }

.dismiss-btn {
  padding: 6px 14px;
  background: transparent;
  color: var(--danger);
  border: 1.5px solid var(--danger);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.dismiss-btn:hover { background: var(--danger-bg); }

.reactivate-btn {
  padding: 6px 14px;
  background: #22c55e;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.reactivate-btn:hover { background: #16a34a; }
</style>
