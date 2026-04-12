<template>
  <div class="collection-header">
    <router-link to="/albums" class="back-link">← {{ t('albums.title') }}</router-link>
    <h1 class="page-title">{{ collection?.name ?? '…' }}</h1>
    <span class="collection-id" v-if="collection">{{ collection.type }} · {{ String(collection.id).padStart(6, '0') }}</span>
  </div>

  <div v-if="loading" class="loading">{{ t('albums.loading') }}</div>

  <div v-else-if="files.length === 0" class="empty">
    <p>{{ t('albums.no_files') }}</p>
  </div>

  <div v-else class="files-grid">
    <router-link
      v-for="f in files"
      :key="f.id"
      :to="f.tile_base_url ? `/albums/${route.params.id}/${f.id}` : ''"
      class="file-card"
      :class="{ 'no-viewer': !f.tile_base_url }"
    >
      <div class="file-thumb">
        <SkeletonThumb v-if="f.status !== 'active'" />
        <img v-else-if="f.preview_url" :src="f.preview_url" class="thumb-img" />
        <div v-else class="thumb-placeholder">{{ t('albums.no_preview') }}</div>
      </div>
      <div class="file-status" :class="`status-${f.status}`">{{ f.status }}</div>
    </router-link>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { apiFetch } from '../api.js'
import SkeletonThumb from '../components/SkeletonThumb.vue'

const { t } = useI18n()
const route = useRoute()

const collection = ref(null)
const files = ref([])
const loading = ref(true)

onMounted(async () => {
  const id = route.params.id
  try {
    const [cRes, fRes] = await Promise.all([
      apiFetch('/collections'),
      apiFetch(`/collections/${id}/files`),
    ])
    const cols = await cRes.json()
    collection.value = cols.find(c => c.id === Number(id)) ?? null
    files.value = await fRes.json()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.collection-header {
  margin-bottom: var(--sp-5);
}
.back-link {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  text-decoration: none;
  display: inline-block;
  margin-bottom: var(--sp-2);
}
.back-link:hover { color: var(--text); }
.collection-id {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  font-family: monospace;
  display: block;
  margin-top: var(--sp-1);
}
.loading, .empty {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  padding: var(--sp-6) 0;
}
.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--sp-3);
}
.file-card {
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  background: var(--surface);
  transition: border-color 0.15s;
  position: relative;
  text-decoration: none;
  color: inherit;
  display: block;
}
.file-card:hover { border-color: var(--accent); }
.file-card.no-viewer { cursor: default; pointer-events: none; }
.file-thumb {
  aspect-ratio: 3/4;
  background: var(--surface-muted);
  overflow: hidden;
}
.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-xs);
  color: var(--text-muted);
}
.file-status {
  font-size: var(--fs-xs);
  padding: var(--sp-1) var(--sp-2);
  color: var(--text-muted);
}
.status-active { color: var(--success); }
.status-new { color: var(--text-muted); }
.status-missing { color: var(--danger); }

</style>
