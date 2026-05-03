<template>
  <ConfirmDialog ref="confirmDialog" />
  <div class="history">
    <div class="history-header">
      <h3>{{ title }}</h3>
      <span v-if="entries.length" class="count">{{ entries.length }} {{ entryWord }}</span>
    </div>

    <p v-if="!entries.length" class="empty">Prašymų dar nėra.</p>

    <ul v-else>
      <li v-for="req in entries" :key="req.id" class="entry">
        <div class="entry-left">
          <span :class="['type-badge', req.type]">
            {{ req.type === 'vacation' ? 'Atostogos' : 'Nedarbingumas' }}
          </span>
          <div class="dates">
            <span class="date-range">{{ req.start_date }} — {{ req.end_date }}</span>
            <span class="days-count">{{ req.days }} {{ daysWord(req.days) }}</span>
          </div>
          <span v-if="req.notes" class="notes">{{ req.notes }}</span>
        </div>
        <div class="entry-right">
          <span :class="['status-badge', req.status]">{{ statusLabel(req.status) }}</span>
          <button
            v-if="req.status === 'pending'"
            class="cancel-btn"
            title="Atšaukti prašymą"
            @click="cancel(req.id)"
          >Atšaukti</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import API from '../api'
import ConfirmDialog from './ConfirmDialog.vue'

const confirmDialog = ref(null)

const props = defineProps({
  title: String,
  entries: Array
})

const emit = defineEmits(['cancelled'])

const entryWord = computed(() => {
  const n = props.entries.length
  if (n % 10 === 1 && n % 100 !== 11) return 'prašymas'
  if (n % 10 >= 2 && n % 10 <= 9 && !(n % 100 >= 12 && n % 100 <= 19)) return 'prašymai'
  return 'prašymų'
})

function daysWord(n) {
  if (n % 10 === 1 && n % 100 !== 11) return 'diena'
  if (n % 10 >= 2 && n % 10 <= 9 && !(n % 100 >= 12 && n % 100 <= 19)) return 'dienos'
  return 'dienų'
}

function statusLabel(s) {
  return { pending: 'Laukiama', approved: 'Patvirtinta', denied: 'Atmesta' }[s] ?? s
}

async function cancel(id) {
  const ok = await confirmDialog.value.show('Ar tikrai norite atšaukti šį prašymą?')
  if (!ok) return
  await API.delete(`/leave/${id}`)
  emit('cancelled')
}
</script>

<style scoped>
.history {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
}

.history-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

h3 { margin: 0; font-size: 15px; }

.count {
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  background: var(--muted);
  padding: 2px 8px;
  border-radius: 99px;
  border: 1px solid var(--border);
}

.empty { color: var(--text); font-size: 13px; margin: 0; }

ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }

.entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  flex-wrap: wrap;
  transition: background 0.12s;
}

.entry:hover { background: var(--muted); }

.entry-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.entry-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

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

.dates { display: flex; align-items: center; gap: 8px; }

.date-range { font-size: 13px; color: var(--text-h); font-weight: 600; white-space: nowrap; }

.days-count {
  font-size: 11px;
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
}

.notes {
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-style: italic;
}

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

.cancel-btn {
  padding: 4px 12px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.cancel-btn:hover { border-color: var(--danger); color: var(--danger); }
</style>
