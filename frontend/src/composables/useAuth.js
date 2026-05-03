import { ref } from 'vue'
import { useRouter } from 'vue-router'
import API from '../api'

const user = ref(null)

export function useAuth() {
  const router = useRouter()

  async function fetchMe() {
    try {
      const res = await API.get('/auth/me')
      user.value = res.data
    } catch {
      user.value = null
    }
  }

  async function login(username, password) {
    const res = await API.post('/auth/login', { username, password })
    user.value = res.data
    const role = res.data.role
    if (role === 'admin') router.push('/admin')
    else if (role === 'manager') router.push('/manager')
    else router.push('/')
  }

  async function logout() {
    await API.post('/auth/logout')
    user.value = null
    router.push('/login')
  }

  return { user, fetchMe, login, logout }
}
