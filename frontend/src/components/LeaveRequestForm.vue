<template>
  <DateRangePicker ref="dateRangePicker" />
  <div class="form-card">
    <h2>Pateikti prašymą</h2>
    <form @submit.prevent="submit">
      <div class="field">
        <label>Laikotarpis</label>
        <button type="button" class="date-btn" @click="pickRange">
          <svg class="date-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" /></svg>
          <span>{{ formatDate(form.start_date) }} — {{ formatDate(form.end_date) }}</span>
        </button>
      </div>

      <div class="field" v-if="duration > 0">
        <span class="duration-hint">{{ duration }} {{ dayWord }}</span>
      </div>

      <div class="field">
        <label>Pastabos <span class="optional">(neprivaloma)</span></label>
        <input v-model="form.notes" type="text" placeholder="Priežastis ar papildoma informacija" />
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Siunčiama…' : 'Pateikti prašymą' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import API from '../api'
import DateRangePicker from './DateRangePicker.vue'

const props = defineProps({ type: { type: String, default: 'vacation' } })
const emit = defineEmits(['submitted'])

const today = new Date().toISOString().split('T')[0]
const form = ref({ start_date: today, end_date: today, notes: '' })
const error = ref('')
const loading = ref(false)
const dateRangePicker = ref(null)

const monthNames = ['sausio','vasario','kovo','balandžio','gegužės','birželio','liepos','rugpjūčio','rugsėjo','spalio','lapkričio','gruodžio']
function formatDate(str) {
  if (!str) return '—'
  const d = new Date(str + 'T00:00:00')
  return `${d.getDate()} ${monthNames[d.getMonth()]} ${d.getFullYear()}`
}

async function pickRange() {
  const result = await dateRangePicker.value.show(form.value.start_date, form.value.end_date, 'Laikotarpis')
  if (result === null) return
  form.value.start_date = result.from
  form.value.end_date   = result.to
}

const duration = computed(() => {
  if (!form.value.start_date || !form.value.end_date) return 0
  const diff = (new Date(form.value.end_date) - new Date(form.value.start_date)) / 86400000
  return diff >= 0 ? diff + 1 : 0
})

const dayWord = computed(() => {
  const n = duration.value
  if (n % 10 === 1 && n % 100 !== 11) return 'diena'
  if (n % 10 >= 2 && n % 10 <= 9 && !(n % 100 >= 12 && n % 100 <= 19)) return 'dienos'
  return 'dienų'
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await API.post('/leave', {
      type: props.type,
      start_date: form.value.start_date,
      end_date: form.value.end_date,
      notes: form.value.notes
    })
    form.value = { start_date: today, end_date: today, notes: '' }
    emit('submitted')
  } catch (e) {
    error.value = e.response?.data?.error || 'Nepavyko pateikti prašymo'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

h2 { margin: 0 0 18px; font-size: 17px; }

form { display: flex; flex-direction: column; gap: 14px; }

.row { display: flex; gap: 12px; }
.row .field { flex: 1; }

.field { display: flex; flex-direction: column; gap: 5px; }

label { font-size: 13px; font-weight: 500; color: var(--text-h); }

.optional { font-weight: 400; color: var(--text); }

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

.date-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 10px 13px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.date-btn:hover { border-color: var(--accent-border); background: var(--accent-bg); }
.date-btn:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-ring); }

.date-icon { width: 16px; height: 16px; color: var(--text); flex-shrink: 0; }

.duration-hint {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-bg);
  padding: 4px 12px;
  border-radius: 99px;
  align-self: flex-start;
  border: 1px solid var(--accent-border);
}

button[type="submit"] {
  padding: 10px 22px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  align-self: flex-start;
  font-family: inherit;
  transition: background 0.15s;
}

button[type="submit"]:hover { background: var(--accent-hover); }
button:disabled { opacity: 0.55; cursor: default; }

.error {
  color: var(--danger);
  font-size: 13px;
  background: var(--danger-bg);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  margin: 0;
}
</style>
