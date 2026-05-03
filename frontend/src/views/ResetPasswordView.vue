<template>
  <div class="page">
    <div class="card">
      <h1>Darbuotojų Apskaita</h1>

      <!-- Invalid / expired token -->
      <template v-if="tokenInvalid">
        <p class="subtitle">Nuoroda negaliojanti arba pasibaigusi.</p>
        <router-link to="/login" class="back-link">← Grįžti į prisijungimą</router-link>
      </template>

      <!-- Success -->
      <template v-else-if="done">
        <div class="success-box">Slaptažodis sėkmingai pakeistas.</div>
        <router-link to="/login" class="back-link">← Prisijungti</router-link>
      </template>

      <!-- Form -->
      <template v-else>
        <p class="subtitle">Įveskite naują slaptažodį</p>
        <form @submit.prevent="submit">
          <div class="field">
            <label>Naujas slaptažodis</label>
            <input v-model="password" type="password" required autocomplete="new-password" minlength="8" />
          </div>
          <div class="field">
            <label>Pakartokite slaptažodį</label>
            <input v-model="confirm" type="password" required autocomplete="new-password" />
          </div>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" :disabled="loading">
            {{ loading ? 'Keičiama…' : 'Keisti slaptažodį' }}
          </button>
        </form>
        <router-link to="/login" class="back-link">← Atgal</router-link>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import API from '../api'

const route        = useRoute()
const token        = ref('')
const password     = ref('')
const confirm      = ref('')
const error        = ref('')
const loading      = ref(false)
const done         = ref(false)
const tokenInvalid = ref(false)

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) tokenInvalid.value = true
})

async function submit() {
  error.value = ''
  if (password.value !== confirm.value) {
    error.value = 'Slaptažodžiai nesutampa'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Slaptažodis turi būti bent 8 simbolių'
    return
  }
  loading.value = true
  try {
    await API.post('/auth/reset-password', { token: token.value, password: password.value })
    done.value = true
  } catch (e) {
    const msg = e.response?.data?.error || ''
    if (e.response?.status === 400 && msg.includes('negaliojanti')) {
      tokenInvalid.value = true
    } else {
      error.value = msg || 'Nepavyko pakeisti slaptažodžio'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page {
  min-height: 100svh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg);
}

.card {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 40px 36px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 0;
}

h1 {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--text-h);
}

.subtitle {
  text-align: center;
  font-size: 13px;
  color: var(--text);
  margin: 0 0 28px;
}

form { display: flex; flex-direction: column; gap: 16px; }

.field { display: flex; flex-direction: column; gap: 5px; }

label { font-size: 13px; font-weight: 500; color: var(--text-h); }

input {
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
  width: 100%;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

button[type="submit"] {
  margin-top: 4px;
  padding: 11px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
  width: 100%;
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

.success-box {
  background: var(--success-bg);
  color: #166534;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 16px;
}

.back-link {
  display: inline-block;
  margin-top: 18px;
  font-size: 13px;
  color: var(--accent);
  text-decoration: none;
}

.back-link:hover { text-decoration: underline; }
</style>
