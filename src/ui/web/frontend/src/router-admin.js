import { createRouter, createWebHistory } from 'vue-router'
import { apiUrl } from './api.js'
import LoginView from './views/LoginView.vue'
import TaskView from './views/admin/TaskView.vue'
import ConfigView from './views/admin/ConfigView.vue'

const routes = [
  { path: '/admin/login', component: LoginView },
  { path: '/admin/config', component: ConfigView, meta: { requiresAuth: true } },
  { path: '/admin/tasks/:task', component: TaskView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/admin/config' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let _initialized = null

router.beforeEach(async (to) => {
  if (_initialized === null) {
    try {
      const res = await fetch(apiUrl('/setup/status'))
      const data = await res.json()
      _initialized = data.initialized
    } catch {
      _initialized = false
    }
  }

  if (!_initialized) {
    window.location.href = '/setup'
    return false
  }

  if (to.path === '/admin/login') return true

  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) return '/admin/login'

    const res = await fetch(apiUrl('/auth/me'), {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) {
      localStorage.removeItem('token')
      return '/admin/login'
    }
  }

  return true
})

export default router
