<template>
  <div class="login-page">
    <div class="login-card">
      <h1>Darbuotojų Apskaita</h1>

      <div v-if="checking" class="status">Tikrinamas pakvietimas…</div>

      <div v-else-if="!inviteValid" class="invalid">
        <p class="error">Ši pakvietimo nuoroda yra negaliojanti arba jos galiojimo laikas baigėsi.</p>
        <router-link to="/login" class="back-link">Grįžti į prisijungimą</router-link>
      </div>

      <template v-else>
        <p class="invite-info">
          Jūs buvote pakviesti kaip <strong>{{ roleLabel }}</strong>.
          Užpildykite formą, kad sukurtumėte paskyrą.
        </p>

        <form @submit.prevent="submit">
          <div class="row">
            <div class="field">
              <label>Vardas</label>
              <input v-model="firstName" type="text" required autocomplete="given-name" />
            </div>
            <div class="field">
              <label>Pavardė</label>
              <input v-model="lastName" type="text" required autocomplete="family-name" />
            </div>
          </div>
          <div class="field">
            <label>Vartotojo vardas</label>
            <input v-model="username" type="text" required autocomplete="username" />
          </div>
          <div class="field">
            <label>Slaptažodis</label>
            <input v-model="password" type="password" required autocomplete="new-password" />
          </div>

          <p v-if="error" class="error">{{ error }}</p>
          <p v-if="success" class="success">{{ success }}</p>

          <button type="submit" :disabled="loading || !!success">
            {{ loading ? 'Kuriama paskyra…' : 'Sukurti paskyrą' }}
          </button>
        </form>

        <p v-if="success" class="toggle-link">
          <router-link to="/login">Eiti į prisijungimą</router-link>
        </p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import API from '../api'

const route = useRoute()
const token = route.query.token

const checking = ref(true)
const inviteValid = ref(false)
const inviteRole = ref('')

const roleLabels = { worker: 'Darbuotojas', manager: 'Vadybininkas', admin: 'Administratorius' }
const roleLabel = computed(() => roleLabels[inviteRole.value] ?? inviteRole.value)

const firstName = ref('')
const lastName = ref('')
const username = ref('')
const password = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

onMounted(async () => {
  if (!token) { checking.value = false; return }
  try {
    const res = await API.get('/auth/invite/validate', { params: { token } })
    inviteValid.value = res.data.valid
    inviteRole.value = res.data.role
  } catch {
    inviteValid.value = false
  } finally {
    checking.value = false
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await API.post('/auth/register', {
      token,
      first_name: firstName.value,
      last_name: lastName.value,
      username: username.value,
      password: password.value
    })
    success.value = 'Paskyra sukurta! Dabar galite prisijungti.'
  } catch (e) {
    error.value = e.response?.data?.error || 'Registracija nepavyko'
  } finally {
    loading.value = false
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
}

.login-card {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 40px 36px;
  box-shadow: var(--shadow-lg);
}

h1 { text-align: center; font-size: 22px; font-weight: 700; margin: 0 0 24px; }

.status { color: var(--text); text-align: center; padding: 16px 0; font-size: 14px; }

.invalid { text-align: center; }

.invite-info {
  font-size: 13px;
  color: var(--text);
  margin-bottom: 20px;
  line-height: 1.6;
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  padding: 10px 14px;
  border-radius: var(--radius-sm);
}

form { display: flex; flex-direction: column; gap: 14px; }

.row { display: flex; gap: 12px; }
.row .field { flex: 1; }

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
}

input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

button[type="submit"] {
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

.toggle-link { text-align: center; margin-top: 16px; font-size: 13px; color: var(--text); }
.toggle-link a, .back-link { color: var(--accent); text-decoration: none; font-weight: 500; }
.back-link { font-size: 14px; }

.error {
  color: var(--danger);
  font-size: 13px;
  background: var(--danger-bg);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  margin: 0;
}
.success {
  color: #065f46;
  font-size: 13px;
  background: var(--success-bg);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  margin: 0;
}
</style>
