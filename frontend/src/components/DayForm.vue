<template>
  <DatePicker ref="datePicker" />
  <div class="form-card">
    <h2>Įvesti {{ label }}</h2>
    <form @submit.prevent="submit">
      <div class="field">
        <label>Data</label>
        <button type="button" class="date-btn" @click="openDatePicker">
          <svg class="date-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" /></svg>
          <span>{{ formatDate(form.date) }}</span>
        </button>
      </div>
      <div class="field">
        <label>Pastabos <span class="optional">(neprivaloma)</span></label>
        <input v-model="form.notes" type="text" :placeholder="placeholder" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">{{ loading ? 'Saugoma…' : `Įvesti ${label}` }}</button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import API from '../api'
import DatePicker from './DatePicker.vue'

const props = defineProps({ type: String })
const emit = defineEmits(['logged'])

const label = computed(() => props.type === 'vacation' ? 'atostogų dieną' : 'nedarbingumo dieną')
const placeholder = computed(() => props.type === 'vacation' ? 'Papildoma informacija?' : 'Simptomai ar priežastis')

const today = new Date().toISOString().split('T')[0]
const form = ref({ date: today, notes: '' })
const error = ref('')
const loading = ref(false)
const datePicker = ref(null)

const monthNames = ['sausio','vasario','kovo','balandžio','gegužės','birželio','liepos','rugpjūčio','rugsėjo','spalio','lapkričio','gruodžio']
function formatDate(str) {
  if (!str) return '—'
  const d = new Date(str + 'T00:00:00')
  return `${d.getDate()} ${monthNames[d.getMonth()]} ${d.getFullYear()}`
}
async function openDatePicker() {
  const result = await datePicker.value.show(form.value.date, 'Data')
  if (result !== null) form.value.date = result
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await API.post(`/${props.type}`, { date: form.value.date, notes: form.value.notes })
    form.value = { date: today, notes: '' }
    emit('logged')
  } catch (e) {
    error.value = e.response?.data?.error || 'Nepavyko išsaugoti'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 24px;
}

h2 { margin: 0 0 16px; font-size: 18px; }

form { display: flex; flex-direction: column; gap: 12px; }

.field { display: flex; flex-direction: column; gap: 4px; }

label { font-size: 13px; font-weight: 500; color: var(--text-h); }

.optional { font-weight: 400; color: var(--text); }

input {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text-h);
  font-size: 14px;
}

input:focus {
  outline: 2px solid var(--accent);
  outline-offset: -1px;
  border-color: transparent;
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

button {
  padding: 9px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  align-self: flex-start;
}

button:disabled { opacity: 0.6; cursor: default; }

.error { color: #ef4444; font-size: 13px; margin: 0; }
</style>
