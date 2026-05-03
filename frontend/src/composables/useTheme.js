import { ref } from 'vue'

const theme = ref(
  typeof localStorage !== 'undefined'
    ? (localStorage.getItem('theme') || 'light')
    : 'light'
)

function apply(t) {
  document.documentElement.setAttribute('data-theme', t)
  localStorage.setItem('theme', t)
  theme.value = t
}

export function useTheme() {
  function toggle() {
    apply(theme.value === 'light' ? 'dark' : 'light')
  }
  return { theme, toggle }
}
