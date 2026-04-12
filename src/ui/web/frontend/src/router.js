import { createRouter, createWebHistory } from 'vue-router'
import { apiUrl } from './api.js'
import LoginView from './views/LoginView.vue'
import AlbumsView from './views/AlbumsView.vue'
import CollectionView from './views/CollectionView.vue'
import FileView from './views/FileView.vue'
import WipView from './views/WipView.vue'
import ConfigView from './views/ConfigView.vue'
import ImportView from './views/ImportView.vue'
import ImportScanView from './views/ImportScanView.vue'
import ServicesView from './views/ServicesView.vue'
import UsersView from './views/UsersView.vue'

const routes = [
  { path: '/login', component: LoginView },
  { path: '/albums', component: AlbumsView, meta: { requiresAuth: true } },
  { path: '/albums/:id', component: CollectionView, meta: { requiresAuth: true } },
  { path: '/albums/:id/:fileId', component: FileView, meta: { requiresAuth: true, viewer: true } },
  { path: '/photos', component: WipView, meta: { requiresAuth: true } },
  { path: '/map', component: WipView, meta: { requiresAuth: true } },
  { path: '/people', component: WipView, meta: { requiresAuth: true } },
  { path: '/genealogy', component: WipView, meta: { requiresAuth: true } },
  { path: '/timeline', component: WipView, meta: { requiresAuth: true } },
  { path: '/stats', component: WipView, meta: { requiresAuth: true } },
  { path: '/settings', component: ConfigView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/import', component: ImportView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/import/scan', component: ImportScanView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/services', component: ServicesView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/users', component: UsersView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/:pathMatch(.*)*', redirect: '/albums' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let _initialized = null
let _user = null

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
    if (to.path !== '/setup') {
      window.location.href = '/setup'
      return false
    }
    return true
  }

  if (to.path === '/setup') return '/login'

  if (to.path === '/login') return true

  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) return '/login'

    if (!_user) {
      const res = await fetch(apiUrl('/auth/me'), {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        localStorage.removeItem('token')
        return '/login'
      }
      _user = await res.json()
    }

    if (to.meta.requiresAdmin && _user.role !== 'admin') {
      return '/albums'
    }
  }

  return true
})

router.afterEach(() => {
  // Reset cached user on logout (token removal)
  if (!localStorage.getItem('token')) _user = null
})

export default router
