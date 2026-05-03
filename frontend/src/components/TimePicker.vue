<template>
  <Teleport to="body">
    <div v-if="visible" class="tp-overlay" @mousedown.self="handleCancel">
      <div class="tp-card">

        <div class="tp-header">
          <button class="tp-cancel" @click="handleCancel">Atšaukti</button>
          <span class="tp-title">{{ title }}</span>
          <button class="tp-confirm" @click="handleConfirm">Patvirtinti</button>
        </div>

        <div class="tp-body">
          <div class="tp-highlight" />

          <div class="tp-col" ref="hourCol" @scroll="onHourScroll"
               @mousedown.prevent="e => startDrag(e, 'hour')"
               @touchstart.passive="e => startDrag(e, 'hour')">
            <div class="tp-pad" />
            <div
              v-for="h in hoursArr"
              :key="h"
              class="tp-item"
              :class="{ active: h === selectedHour }"
              @click="clickHour(h)"
            >{{ pad(h) }}</div>
            <div class="tp-pad" />
          </div>

          <div class="tp-colon">:</div>

          <div class="tp-col" ref="minCol" @scroll="onMinScroll"
               @mousedown.prevent="e => startDrag(e, 'min')"
               @touchstart.passive="e => startDrag(e, 'min')">
            <div class="tp-pad" />
            <div
              v-for="m in minsArr"
              :key="m"
              class="tp-item"
              :class="{ active: m === selectedMin }"
              @click="clickMin(m)"
            >{{ pad(m) }}</div>
            <div class="tp-pad" />
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'

const ITEM_H = 46
const VISIBLE = 5
const COL_H = ITEM_H * VISIBLE
const PAD_H = (COL_H - ITEM_H) / 2

const hoursArr = Array.from({ length: 24 }, (_, i) => i)
const minsArr  = Array.from({ length: 12 }, (_, i) => i * 5)

const visible      = ref(false)
const title        = ref('Laikas')
const selectedHour = ref(8)
const selectedMin  = ref(0)
const hourCol      = ref(null)
const minCol       = ref(null)

let resolve = null

function pad(n) { return String(n).padStart(2, '0') }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

async function show(time = '08:00', label = 'Laikas') {
  title.value = label
  const [h, m] = time.split(':').map(Number)
  selectedHour.value = h
  // snap minute to nearest 5-min interval
  selectedMin.value = minsArr.reduce((prev, cur) =>
    Math.abs(cur - m) < Math.abs(prev - m) ? cur : prev
  )
  visible.value = true
  await nextTick()
  hourCol.value.scrollTop = hoursArr.indexOf(selectedHour.value) * ITEM_H
  minCol.value.scrollTop  = minsArr.indexOf(selectedMin.value)  * ITEM_H
  return new Promise(r => { resolve = r })
}

function onHourScroll() {
  const idx = clamp(Math.round(hourCol.value.scrollTop / ITEM_H), 0, hoursArr.length - 1)
  selectedHour.value = hoursArr[idx]
}

function onMinScroll() {
  const idx = clamp(Math.round(minCol.value.scrollTop / ITEM_H), 0, minsArr.length - 1)
  selectedMin.value = minsArr[idx]
}

function clickHour(h) {
  hourCol.value.scrollTo({ top: hoursArr.indexOf(h) * ITEM_H, behavior: 'smooth' })
}

function clickMin(m) {
  minCol.value.scrollTo({ top: minsArr.indexOf(m) * ITEM_H, behavior: 'smooth' })
}

let dragState = null

function startDrag(e, which) {
  const col = which === 'hour' ? hourCol.value : minCol.value
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  dragState = { which, col, startY: clientY, startTop: col.scrollTop, moved: false }

  function onMove(ev) {
    const y = ev.touches ? ev.touches[0].clientY : ev.clientY
    const delta = dragState.startY - y
    if (Math.abs(delta) > 2) dragState.moved = true
    dragState.col.scrollTop = dragState.startTop + delta
  }

  function onEnd() {
    if (dragState) snapNearest(dragState.which)
    dragState = null
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onEnd)
    window.removeEventListener('touchmove', onMove)
    window.removeEventListener('touchend', onEnd)
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onEnd)
  window.addEventListener('touchmove', onMove, { passive: true })
  window.addEventListener('touchend', onEnd)
}

function snapNearest(which) {
  const col = which === 'hour' ? hourCol.value : minCol.value
  const arr = which === 'hour' ? hoursArr : minsArr
  const idx = clamp(Math.round(col.scrollTop / ITEM_H), 0, arr.length - 1)
  col.scrollTo({ top: idx * ITEM_H, behavior: 'smooth' })
}

function handleConfirm() {
  visible.value = false
  resolve?.(`${pad(selectedHour.value)}:${pad(selectedMin.value)}`)
}

function handleCancel() {
  visible.value = false
  resolve?.(null)
}

function onKeydown(e) {
  if (!visible.value) return
  if (e.key === 'Escape') handleCancel()
  if (e.key === 'Enter') handleConfirm()
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

defineExpose({ show })
</script>

<style scoped>
.tp-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(2px);
}

.tp-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 300px;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

/* ── Header ── */
.tp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
}

.tp-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-h);
}

.tp-cancel, .tp-confirm {
  background: none;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  padding: 2px 0;
}

.tp-cancel { color: var(--text); }
.tp-cancel:hover { color: var(--text-h); }

.tp-confirm { color: var(--accent); }
.tp-confirm:hover { color: var(--accent-hover); }

/* ── Picker body ── */
.tp-body {
  position: relative;
  display: flex;
  align-items: center;
  height: v-bind('COL_H + "px"');
  padding: 0 24px;
  gap: 0;
}

/* Selection highlight lines */
.tp-highlight {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  height: v-bind('ITEM_H + "px"');
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  pointer-events: none;
  z-index: 2;
}

/* ── Column ── */
.tp-col {
  flex: 1;
  height: v-bind('COL_H + "px"');
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-overflow-scrolling: touch;
  cursor: grab;
  user-select: none;
  mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(0,0,0,0.25) 18%,
    black 34%,
    black 66%,
    rgba(0,0,0,0.25) 82%,
    transparent 100%
  );
  -webkit-mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(0,0,0,0.25) 18%,
    black 34%,
    black 66%,
    rgba(0,0,0,0.25) 82%,
    transparent 100%
  );
}

.tp-col::-webkit-scrollbar { display: none; }

.tp-pad {
  height: v-bind('PAD_H + "px"');
  flex-shrink: 0;
  scroll-snap-align: none;
}

/* ── Items ── */
.tp-item {
  height: v-bind('ITEM_H + "px"');
  display: flex;
  align-items: center;
  justify-content: center;
  scroll-snap-align: center;
  font-size: 19px;
  font-weight: 400;
  color: var(--text);
  cursor: pointer;
  user-select: none;
  transition: color 0.12s, font-weight 0.12s, font-size 0.12s;
  font-variant-numeric: tabular-nums;
}

.tp-item.active {
  color: var(--text-h);
  font-weight: 600;
  font-size: 21px;
}

/* ── Colon separator ── */
.tp-colon {
  font-size: 22px;
  font-weight: 300;
  color: var(--text-h);
  padding: 0 6px;
  flex-shrink: 0;
  z-index: 3;
  pointer-events: none;
  margin-bottom: 2px;
}
</style>
