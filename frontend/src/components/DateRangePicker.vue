<template>
  <Teleport to="body">
    <div v-if="visible" class="dp-overlay" @mousedown.self="handleCancel">
      <div class="dp-card">

        <div class="dp-header">
          <button class="dp-cancel" @click="handleCancel">Atšaukti</button>
          <span class="dp-title">{{ title }}</span>
          <button class="dp-confirm" :disabled="!rangeStart" @click="handleConfirm">Patvirtinti</button>
        </div>

        <div class="dp-range-bar">
          <span :class="['dp-range-val', phase === 1 ? 'active' : '']">
            {{ rangeStart ? formatShort(rangeStart) : 'Nuo…' }}
          </span>
          <span class="dp-bar-sep">→</span>
          <span :class="['dp-range-val', phase === 2 ? 'active' : '']">
            {{ effectiveEnd ? formatShort(effectiveEnd) : 'Iki…' }}
          </span>
        </div>

        <div class="dp-nav">
          <button class="dp-nav-btn" @click="prevMonth">&#8249;</button>
          <span class="dp-month-label">{{ monthLabel }} {{ viewYear }}</span>
          <button class="dp-nav-btn" @click="nextMonth">&#8250;</button>
        </div>

        <div class="dp-weekdays">
          <span v-for="d in weekdays" :key="d">{{ d }}</span>
        </div>

        <div class="dp-grid" @mouseleave="hoverDate = null">
          <button
            v-for="cell in cells"
            :key="cell.key"
            class="dp-day"
            :class="{
              empty: !cell.day,
              today: cell.isToday && !cell.isRangeStart && !cell.isRangeEnd && !cell.isSingle,
              'range-start': cell.isRangeStart,
              'range-end': cell.isRangeEnd,
              'in-range': cell.inRange,
              'is-single': cell.isSingle,
            }"
            :disabled="!cell.day"
            @click="cell.day && selectDay(cell.key)"
            @mouseenter="cell.day && (hoverDate = cell.key)"
          ><span>{{ cell.day ?? '' }}</span></button>
        </div>

        <p class="dp-hint">
          {{ phase === 1 ? 'Pasirinkite pradžios datą' : 'Pasirinkite pabaigos datą' }}
        </p>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'

const visible    = ref(false)
const title      = ref('Laikotarpis')
const phase      = ref(1)
const rangeStart = ref('')
const rangeEnd   = ref('')
const hoverDate  = ref(null)

const today    = new Date()
const todayStr = today.toISOString().split('T')[0]
const viewYear  = ref(today.getFullYear())
const viewMonth = ref(today.getMonth())

let resolve = null

const weekdays   = ['Pr', 'An', 'Tr', 'Kt', 'Pn', 'Št', 'Sk']
const monthNames = ['Sausis','Vasaris','Kovas','Balandis','Gegužė','Birželis','Liepa','Rugpjūtis','Rugsėjis','Spalis','Lapkritis','Gruodis']
const monthNamesShort = ['saus.','vas.','kov.','bal.','geg.','birž.','liepos','rugpj.','rugsėj.','spal.','lapkr.','gruod.']

const monthLabel = computed(() => monthNames[viewMonth.value])

function formatShort(str) {
  if (!str) return ''
  const d = new Date(str + 'T00:00:00')
  return `${d.getDate()} ${monthNamesShort[d.getMonth()]}`
}

const effectiveEnd = computed(() => {
  if (rangeEnd.value) return rangeEnd.value
  if (phase.value === 2 && hoverDate.value) return hoverDate.value
  return null
})

const cells = computed(() => {
  const year  = viewYear.value
  const month = viewMonth.value
  const first  = new Date(year, month, 1).getDay()
  const offset = (first + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const result = []

  let lo = rangeStart.value || null
  let hi = effectiveEnd.value || null
  if (lo && hi && lo > hi) [lo, hi] = [hi, lo]

  for (let i = 0; i < offset; i++) {
    result.push({ key: `e${i}`, day: null })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const isStart  = !!lo && dateStr === lo
    const isEnd    = !!hi && dateStr === hi
    const isSingle = isStart && isEnd
    result.push({
      key: dateStr,
      day: d,
      isToday: dateStr === todayStr,
      isRangeStart: isStart && !isSingle,
      isRangeEnd:   isEnd   && !isSingle,
      inRange: !!lo && !!hi && dateStr > lo && dateStr < hi,
      isSingle,
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

function selectDay(dateStr) {
  if (phase.value === 1) {
    rangeStart.value = dateStr
    rangeEnd.value   = ''
    phase.value      = 2
  } else {
    let from = rangeStart.value
    let to   = dateStr
    if (from > to) [from, to] = [to, from]
    visible.value   = false
    hoverDate.value = null
    resolve?.({ from, to })
  }
}

function handleConfirm() {
  if (!rangeStart.value) return
  const from = rangeStart.value
  const to   = rangeEnd.value || rangeStart.value
  const lo   = from <= to ? from : to
  const hi   = from <= to ? to   : from
  visible.value   = false
  hoverDate.value = null
  resolve?.({ from: lo, to: hi })
}

function handleCancel() {
  visible.value   = false
  hoverDate.value = null
  resolve?.(null)
}

async function show(fromStr = '', toStr = '', label = 'Laikotarpis') {
  title.value      = label
  rangeStart.value = fromStr || ''
  rangeEnd.value   = toStr   || ''
  hoverDate.value  = null
  phase.value      = 1

  const d = fromStr ? new Date(fromStr + 'T00:00:00') : new Date()
  viewYear.value  = d.getFullYear()
  viewMonth.value = d.getMonth()

  visible.value = true
  await nextTick()
  return new Promise(r => { resolve = r })
}

function onKeydown(e) {
  if (!visible.value) return
  if (e.key === 'Escape') handleCancel()
  if (e.key === 'Enter' && rangeStart.value) handleConfirm()
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
  width: min(320px, calc(100vw - 32px));
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

.dp-title { font-size: 14px; font-weight: 600; color: var(--text-h); }

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
.dp-confirm:disabled { opacity: 0.4; cursor: default; }

/* ── Range bar ── */
.dp-range-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 18px;
  border-bottom: 1px solid var(--border);
  background: var(--muted);
}

.dp-range-val {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  padding: 3px 10px;
  border-radius: var(--radius-sm);
  transition: background 0.15s, color 0.15s;
  min-width: 70px;
  text-align: center;
}

.dp-range-val.active {
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent-border);
}

.dp-bar-sep { font-size: 14px; color: var(--text); }

/* ── Month nav ── */
.dp-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px 8px;
}

.dp-month-label { font-size: 14px; font-weight: 600; color: var(--text-h); }

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
  padding: 0 12px 12px;
  gap: 0;
}

.dp-day {
  position: relative;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  padding: 0;
}

/* Inner circle element (day number) */
.dp-day span {
  position: relative;
  z-index: 1;
  width: 80%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 400;
  color: var(--text-h);
  border-radius: 50%;
  transition: background 0.1s, color 0.1s;
}

/* Hover */
.dp-day:hover:not(.empty):not(.range-start):not(.range-end):not(.is-single) span {
  background: var(--muted);
}

/* Today */
.dp-day.today span {
  background: var(--accent-bg);
  color: var(--accent);
  font-weight: 600;
}

/* ── Range strip ── */
.dp-day.in-range {
  background: var(--accent-bg);
}

.dp-day.in-range span {
  color: var(--accent);
  background: transparent;
}

/* Start: right half gets strip color, left half transparent */
.dp-day.range-start {
  background: linear-gradient(to right, transparent 50%, var(--accent-bg) 50%);
}

/* End: left half gets strip color, right half transparent */
.dp-day.range-end {
  background: linear-gradient(to left, transparent 50%, var(--accent-bg) 50%);
}

/* Accent circle for selected endpoints */
.dp-day.range-start span,
.dp-day.range-end span,
.dp-day.is-single span {
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}

.dp-day.today.in-range span { font-weight: 700; }

.dp-day.empty {
  cursor: default;
  pointer-events: none;
}

.dp-day:disabled { cursor: default; }

/* ── Hint ── */
.dp-hint {
  font-size: 11px;
  color: var(--text);
  text-align: center;
  padding: 4px 18px 14px;
  margin: 0;
}
</style>
