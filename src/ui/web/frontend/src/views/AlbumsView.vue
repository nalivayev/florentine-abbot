<template>
  <h1 class="page-title">{{ t('albums.title') }}</h1>

  <div v-if="loading" class="loading">{{ t('albums.loading') }}</div>

  <div v-else-if="collections.length === 0" class="empty">
    <p class="empty-text">{{ t('albums.empty') }}</p>
    <router-link to="/import" class="btn">{{ t('albums.import_btn') }}</router-link>
  </div>

  <div v-else class="collections-grid">
    <router-link
      v-for="c in collections"
      :key="c.id"
      :to="`/albums/${c.id}`"
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
import { apiFetch } from '../api.js'
import SkeletonThumb from '../components/SkeletonThumb.vue'

const { t } = useI18n()

const collections = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await apiFetch('/collections')
    const data = await res.json()

    // For each collection fetch first file to get cover
    const withCovers = await Promise.all(data.map(async (c) => {
      try {
        const fRes = await apiFetch(`/collections/${c.id}/files`)
        const files = await fRes.json()
        const first = files[0]
        const cover_url = first?.status === 'active' ? first.preview_url : null
        const processing = first?.status !== 'active'
        return { ...c, cover_url, processing }
      } catch {
        return { ...c, cover_url: null, processing: false }
      }
    }))

    collections.value = withCovers
  } catch {
    collections.value = []
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
  border-radius: 8px;
  overflow: hidden;
  text-decoration: none;
  background: var(--surface);
  transition: border-color 0.15s;
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
