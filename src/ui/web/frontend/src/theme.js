import { ref } from 'vue'

const isDark = ref(false)

export function useTheme() {
  function init() {
    isDark.value = localStorage.getItem('theme') === 'dark'
    apply()
  }

  function toggle() {
    isDark.value = !isDark.value
    apply()
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  function apply() {
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  }

  return { isDark, init, toggle }
}
