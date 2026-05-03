<template>
  <div class="login-page">
    <div class="theme-corner"><ThemeToggle /></div>
    <div class="login-card">
      <h1>Darbuotojų Apskaita</h1>

      <!-- Forgot password mode -->
      <template v-if="forgotMode">
        <p class="subtitle">Įveskite el. paštą — atsiųsime nuorodą</p>
        <form @submit.prevent="sendReset">
          <div class="field">
            <label>El. paštas</label>
            <input v-model="resetEmail" type="email" required autocomplete="email" />
          </div>
          <p v-if="resetMsg" class="info">{{ resetMsg }}</p>
          <p v-if="resetError" class="error">{{ resetError }}</p>
          <button type="submit" :disabled="resetLoading">
            {{ resetLoading ? 'Siunčiama…' : 'Siųsti nuorodą' }}
          </button>
        </form>
        <button class="text-btn" @click="forgotMode = false">← Grįžti</button>
      </template>

      <!-- Login mode -->
      <template v-else>
        <p class="subtitle">Prisijunkite prie savo paskyros</p>
        <form @submit.prevent="handleSubmit">
          <div class="field">
            <label>Vartotojo vardas</label>
            <input v-model="username" type="text" required autocomplete="username" />
          </div>
          <div class="field">
            <label>Slaptažodis</label>
            <input v-model="password" type="password" required autocomplete="current-password" />
          </div>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" :disabled="loading">
            {{ loading ? 'Jungiamasi…' : 'Prisijungti' }}
          </button>
        </form>
        <button class="text-btn" @click="openForgot">Pamiršote slaptažodį?</button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth'
import API from '../api'
import ThemeToggle from '../components/ThemeToggle.vue'

const { login } = useAuth()

const username = ref('')
const password = ref('')
const error    = ref('')
const loading  = ref(false)

const forgotMode  = ref(false)
const resetEmail  = ref('')
const resetMsg    = ref('')
const resetError  = ref('')
const resetLoading = ref(false)

async function handleSubmit() {
  error.value   = ''
  loading.value = true
  try {
    await login(username.value, password.value)
  } catch (e) {
    error.value = e.response?.data?.error || 'Prisijungti nepavyko'
  } finally {
    loading.value = false
  }
}

function openForgot() {
  resetEmail.value = ''
  resetMsg.value   = ''
  resetError.value = ''
  forgotMode.value = true
}

async function sendReset() {
  resetMsg.value   = ''
  resetError.value = ''
  resetLoading.value = true
  try {
    const res = await API.post('/auth/forgot-password', { email: resetEmail.value })
    resetMsg.value = res.data.message
  } catch (e) {
    resetError.value = e.response?.data?.error || 'Nepavyko išsiųsti'
  } finally {
    resetLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100svh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg);
  position: relative;
}

.theme-corner {
  position: absolute;
  top: 16px;
  left: 16px;
}

.login-card {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 40px 36px;
  box-shadow: var(--shadow-lg);
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

.text-btn {
  display: block;
  margin-top: 16px;
  width: 100%;
  background: none;
  border: none;
  color: var(--accent);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  text-align: center;
  padding: 0;
}

.text-btn:hover { text-decoration: underline; }

.error {
  color: var(--danger);
  font-size: 13px;
  background: var(--danger-bg);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  margin: 0;
}

.info {
  color: #166534;
  font-size: 13px;
  background: var(--success-bg);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  margin: 0;
}
</style>
