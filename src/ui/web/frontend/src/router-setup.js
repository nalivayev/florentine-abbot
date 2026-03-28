import { createRouter, createWebHistory } from 'vue-router'
import { apiUrl } from './api.js'
import SetupView from './views/SetupView.vue'

const routes = [
  { path: '/setup', component: SetupView },
  { path: '/:pathMatch(.*)*', redirect: '/setup' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let _initialized = null

router.beforeEach(async () => {
  if (_initialized === null) {
    try {
      const res = await fetch(apiUrl('/setup/status'))
      const data = await res.json()
      _initialized = data.initialized
    } catch {
      // server unavailable — stay on setup
      _initialized = false
    }
  }
  if (_initialized) {
    window.location.href = '/admin/login'
    return false
  }
  return true
})

export default router
