<template>
  <Teleport to="body">
    <div v-if="visible" class="dp-overlay" @mousedown.self="handleCancel">
      <div class="dp-card">

        <div class="dp-header">
          <button class="dp-cancel" @click="handleCancel">Atšaukti</button>
          <span class="dp-title">{{ title }}</span>
          <button class="dp-confirm" @click="handleConfirm">Patvirtinti</button>
        </div>

        <div class="dp-nav">
          <button class="dp-nav-btn" @click="prevMonth">&#8249;</button>
          <span class="dp-month-label">{{ monthLabel }} {{ viewYear }}</span>
          <button class="dp-nav-btn" @click="nextMonth">&#8250;</button>
        </div>

        <div class="dp-weekdays">
          <span v-for="d in weekdays" :key="d">{{ d }}</span>
        </div>

        <div class="dp-grid">
          <button
            v-for="cell in cells"
            :key="cell.key"
            class="dp-day"
            :class="{
              empty: !cell.day,
              today: cell.isToday,
              selected: cell.isSelected,
              faded: cell.faded
            }"
            :disabled="!cell.day"
            @click="cell.day && selectDay(cell)"
          >{{ cell.day ?? '' }}</button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'

const visible = ref(false)
const title   = ref('Data')

const today = new Date()
const todayStr = today.toISOString().split('T')[0]

const viewYear  = ref(today.getFullYear())
const viewMonth = ref(today.getMonth()) // 0-based
const selected  = ref(todayStr)

let resolve = null

const weekdays  = ['Pr', 'An', 'Tr', 'Kt', 'Pn', 'Št', 'Sk']
const monthNames = [
  'Sausis','Vasaris','Kovas','Balandis','Gegužė','Birželis',
  'Liepa','Rugpjūtis','Rugsėjis','Spalis','Lapkritis','Gruodis'
]

const monthLabel = computed(() => monthNames[viewMonth.value])

const cells = computed(() => {
  const year  = viewYear.value
  const month = viewMonth.value
  const first = new Date(year, month, 1).getDay() // 0=Sun
  // convert Sun-start to Mon-start
  const offset = (first + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const result = []

  for (let i = 0; i < offset; i++) {
    result.push({ key: `e${i}`, day: null, faded: true })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    result.push({
      key: dateStr,
      day: d,
      isToday: dateStr === todayStr,
      isSelected: dateStr === selected.value,
      faded: false
    })
  }
  return result
})

function prevMonth() {
  if (viewMonth.value === 0) { viewMonth.value = 11; viewYear.value-- }
  else viewMonth.value--
}

function nextMonth() {
  if (viewMonth.value === 11) { viewMonth.value = 0; viewYear.value++ }
  else viewMonth.value++
}

function selectDay(cell) {
  const dateStr = `${viewYear.value}-${String(viewMonth.value + 1).padStart(2, '0')}-${String(cell.day).padStart(2, '0')}`
  selected.value = dateStr
}

async function show(dateStr = todayStr, label = 'Data') {
  title.value = label
  selected.value = dateStr
  const d = new Date(dateStr + 'T00:00:00')
  viewYear.value  = d.getFullYear()
  viewMonth.value = d.getMonth()
  visible.value = true
  await nextTick()
  return new Promise(r => { resolve = r })
}

function handleConfirm() {
  visible.value = false
  resolve?.(selected.value)
}

function handleCancel() {
  visible.value = false
  resolve?.(null)
}

function onKeydown(e) {
  if (!visible.value) return
  if (e.key === 'Escape') handleCancel()
  if (e.key === 'Enter')  handleConfirm()
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

defineExpose({ show })
</script>

<style scoped>
.dp-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(2px);
}

.dp-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 320px;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

/* ── Header ── */
.dp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
}

.dp-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-h);
}

.dp-cancel, .dp-confirm {
  background: none;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  padding: 2px 0;
}

.dp-cancel { color: var(--text); }
.dp-cancel:hover { color: var(--text-h); }
.dp-confirm { color: var(--accent); }
.dp-confirm:hover { color: var(--accent-hover); }

/* ── Month nav ── */
.dp-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px 8px;
}

.dp-month-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-h);
}

.dp-nav-btn {
  background: none;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--text);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  line-height: 1;
  font-family: inherit;
}

.dp-nav-btn:hover { border-color: var(--accent); color: var(--accent); }

/* ── Weekday row ── */
.dp-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: 4px 12px 6px;
  gap: 2px;
}

.dp-weekdays span {
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ── Day grid ── */
.dp-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: 0 12px 16px;
  gap: 3px;
}

.dp-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  font-size: 13px;
  font-weight: 400;
  color: var(--text-h);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.12s, color 0.12s;
}

.dp-day:hover:not(.empty):not(.selected) { background: var(--muted); }

.dp-day.today:not(.selected) {
  background: var(--accent-bg);
  color: var(--accent);
  font-weight: 600;
}

.dp-day.selected {
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}

.dp-day.empty {
  cursor: default;
  pointer-events: none;
}

.dp-day:disabled { cursor: default; }
</style>
