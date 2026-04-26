<template>
  <h1 class="page-title">{{ t('collections.title') }}</h1>

  <div v-if="loading" class="loading">{{ t('collections.loading') }}</div>

  <div v-else-if="collections.length === 0" class="empty">
    <p class="empty-text">{{ t('collections.empty') }}</p>
    <router-link to="/import" class="btn">{{ t('collections.import_btn') }}</router-link>
  </div>

  <div v-else class="collections-grid">
    <router-link
      v-for="c in collections"
      :key="c.id"
      :to="`/collections/${c.id}`"
      class="collection-card"
    >
      <div class="collection-cover">
        <img v-if="c.cover_url" :src="c.cover_url" class="cover-img" />
        <SkeletonThumb v-else-if="c.processing" />
        <div v-else class="cover-placeholder">{{ String(c.id).padStart(6, '0') }}</div>
      </div>
      <div class="collection-info">
        <span class="collection-name">{{ c.name }}</span>
        <span class="collection-meta">{{ c.type }} · {{ String(c.id).padStart(6, '0') }}</span>
      </div>
    </router-link>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../api.js'
import { replaceForRouteFailure, ROUTE_LOAD_TIMEOUT_MS } from '../routeErrors.js'
import SkeletonThumb from '../components/SkeletonThumb.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const collections = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await apiFetch('/collections', { timeoutMs: ROUTE_LOAD_TIMEOUT_MS })
    if (!res.ok) {
      await replaceForRouteFailure(router, route, res)
      return
    }

    const data = await res.json()

    const withCovers = await Promise.all(data.map(async (collection) => {
      try {
        const fileResponse = await apiFetch(`/collections/${collection.id}/files`, { timeoutMs: ROUTE_LOAD_TIMEOUT_MS })
        if (!fileResponse.ok) return { ...collection, cover_url: null, processing: false }
        const files = await fileResponse.json()
        const first = files[0]
        const cover_url = first?.status === 'active' ? first.preview_url : null
        const processing = first?.status !== 'active'
        return { ...collection, cover_url, processing }
      } catch {
        return { ...collection, cover_url: null, processing: false }
      }
    }))

    collections.value = withCovers
  } catch (error) {
    await replaceForRouteFailure(router, route, error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.loading {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  padding: var(--sp-6) 0;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  gap: var(--sp-4);
  color: var(--text-muted);
}
.empty-text { font-size: var(--fs-base); }
.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--sp-4);
}
.collection-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  text-decoration: none;
  background: var(--surface);
  transition: border-color var(--motion-base);
}
.collection-card:hover { border-color: var(--accent); }
.collection-cover {
  aspect-ratio: 3/4;
  background: var(--surface-muted);
  overflow: hidden;
}
.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text-muted);
}
.collection-info {
  padding: var(--sp-3);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}
.collection-name {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.collection-meta {
  font-size: var(--fs-xs);
  color: var(--text-muted);
}
</style>