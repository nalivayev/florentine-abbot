import { createRouter, createWebHistory } from 'vue-router'
import { apiUrl } from './api.js'
import TaskView from './views/admin/TaskView.vue'
import ConfigView from './views/admin/ConfigView.vue'
import LoginView from './views/LoginView.vue'
import SetupView from './views/SetupView.vue'

const routes = [
  { path: '/login', component: LoginView },
  { path: '/setup', component: SetupView },
  { path: '/admin/tasks/:task', component: TaskView, meta: { requiresAuth: true } },
  { path: '/admin/config', component: ConfigView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/admin/tasks/organizer' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  // Check initialization status
  let initialized = false
  let importStatus = 'none'
  try {
    const res = await fetch(apiUrl('/setup/status'))
    const data = await res.json()
    initialized = data.initialized
    importStatus = data.import_status || 'none'
  } catch {
    initialized = false
  }

  const setupPending = !initialized || ['running', 'done', 'interrupted'].includes(importStatus)
  if (setupPending) {
    return to.path === '/setup' ? true : '/setup'
  }

  if (to.path === '/setup') return '/login'
  if (to.path === '/login') return true

  // Check auth
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) return '/login'

    const res = await fetch(apiUrl('/auth/me'), {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) {
      localStorage.removeItem('token')
      return '/login'
    }
  }

  return true
})

export default router
