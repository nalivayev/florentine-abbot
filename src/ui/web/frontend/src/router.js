import { createRouter, createWebHistory } from 'vue-router'
import { apiUrl } from './api.js'
import LoginView from './views/LoginView.vue'
import CollectionsView from './views/CollectionsView.vue'
import CollectionView from './views/CollectionView.vue'
import ErrorView from './views/ErrorView.vue'
import FileView from './views/FileView.vue'
import MapView from './views/MapView.vue'
import NotFoundView from './views/NotFoundView.vue'
import PeopleReviewView from './views/admin/PeopleReviewView.vue'
import WipView from './views/WipView.vue'
import ConfigView from './views/admin/ConfigView.vue'
import ImportView from './views/admin/ImportView.vue'
import ImportScanView from './views/admin/ImportScanView.vue'
import ServicesView from './views/admin/ServicesView.vue'
import FileManagerView from './views/admin/FileManagerView.vue'
import TasksView from './views/admin/TasksView.vue'
import UsersView from './views/admin/UsersView.vue'

const routes = [
  { path: '/login', component: LoginView },
  { path: '/collections', component: CollectionsView, meta: { requiresAuth: true } },
  { path: '/collections/:id', component: CollectionView, meta: { requiresAuth: true } },
  { path: '/collections/:id/:fileId', component: FileView, meta: { requiresAuth: true, viewer: true } },
  { path: '/error', name: 'error', component: ErrorView, meta: { requiresAuth: true } },
  { path: '/not-found', name: 'not-found', component: NotFoundView, meta: { requiresAuth: true } },
  { path: '/photos', component: WipView, meta: { requiresAuth: true } },
  { path: '/map', component: MapView, meta: { requiresAuth: true, viewer: true } },
  { path: '/people', component: PeopleReviewView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/genealogy', component: WipView, meta: { requiresAuth: true } },
  { path: '/timeline', component: WipView, meta: { requiresAuth: true } },
  { path: '/stats', component: WipView, meta: { requiresAuth: true } },
  { path: '/settings', component: ConfigView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/import', component: ImportView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/import/scan', component: ImportScanView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/services', component: ServicesView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/file-manager', component: FileManagerView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/tasks', component: TasksView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/users', component: UsersView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/:pathMatch(.*)*', component: NotFoundView, meta: { requiresAuth: true } },
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
      return '/collections'
    }
  }

  return true
})

router.afterEach(() => {
  // Reset cached user on logout (token removal)
  if (!localStorage.getItem('token')) _user = null
})

export default router
