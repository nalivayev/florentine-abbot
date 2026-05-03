<template>
  <section class="people-review">
    <header class="people-review-hero">
      <div>
        <h1 class="page-title">{{ t('people_review.title') }}</h1>
        <p class="page-subtitle">{{ t('people_review.subtitle') }}</p>
      </div>

      <div class="people-review-summary" v-if="!loading && !loadError && clusters.length > 0">
        <span class="people-review-summary-label">{{ t('people_review.cluster_count', { count: clusters.length }) }}</span>
        <span class="people-review-summary-label">{{ t('people_review.face_total', { count: totalFaces }) }}</span>
      </div>
    </header>

    <div v-if="loading" class="people-review-empty people-review-empty-loading">
      <p>{{ t('people_review.loading') }}</p>
    </div>

    <div v-else-if="loadError" class="error-block">
      {{ loadError }}
    </div>

    <div v-else-if="clusters.length === 0" class="people-review-empty people-review-empty-ready">
      <div class="people-review-empty-card">
        <span class="people-review-empty-badge">{{ t('people_review.ready_badge') }}</span>
        <h2 class="people-review-empty-title">{{ t('people_review.empty_title') }}</h2>
        <p class="people-review-empty-text">{{ t('people_review.empty_text') }}</p>
      </div>
    </div>

    <div v-else class="people-review-layout">
      <aside class="people-review-rail">
        <button
          v-for="cluster in clusters"
          :key="cluster.id"
          type="button"
          class="people-review-cluster"
          :class="{ active: cluster.id === selectedClusterId }"
          @click="selectedClusterId = cluster.id"
        >
          <div class="people-review-cluster-header">
            <span class="people-review-cluster-tag">{{ t('people_review.cluster_label', { id: cluster.id }) }}</span>
            <span class="people-review-cluster-meta">{{ t('people_review.face_count', { count: cluster.face_count }) }}</span>
          </div>

          <div class="people-review-cluster-strip">
            <div
              v-for="face in cluster.faces.slice(0, 4)"
              :key="face.id"
              class="people-review-cluster-strip-item"
            >
              <img v-if="face.thumb_url" :src="face.thumb_url" alt="" class="people-review-cluster-strip-thumb">
              <span v-else class="people-review-cluster-strip-fallback">{{ face.id }}</span>
            </div>
          </div>

          <div class="people-review-cluster-footer">
            <span>{{ t('people_review.assigned_faces', { count: cluster.assigned_face_count }) }}</span>
            <span>{{ t('people_review.distinct_people', { count: cluster.distinct_person_count }) }}</span>
          </div>
        </button>
      </aside>

      <section v-if="selectedCluster" class="people-review-detail">
        <div class="people-review-detail-header">
          <div>
            <p class="people-review-detail-kicker">{{ t('people_review.review_kicker') }}</p>
            <h2 class="people-review-detail-title">{{ t('people_review.cluster_label', { id: selectedCluster.id }) }}</h2>
          </div>

          <div class="people-review-detail-stats">
            <span class="people-review-stat-pill">{{ t('people_review.face_count', { count: selectedCluster.face_count }) }}</span>
            <span class="people-review-stat-pill">{{ t('people_review.assigned_faces', { count: selectedCluster.assigned_face_count }) }}</span>
          </div>
        </div>

        <p class="people-review-detail-text">{{ t('people_review.detail_text') }}</p>

        <div v-if="actionError" class="error-block people-review-action-error">
          {{ actionError }}
        </div>

        <div class="people-review-actions">
          <section class="people-review-action-card">
            <h3 class="people-review-action-title">{{ t('people_review.assign_existing_title') }}</h3>
            <p class="people-review-action-text">{{ t('people_review.assign_existing_text') }}</p>

            <select v-model="selectedPersonId" class="people-review-select" :disabled="isBusy || people.length === 0">
              <option value="">{{ t('people_review.select_person') }}</option>
              <option v-for="person in people" :key="person.id" :value="String(person.id)">
                {{ personLabel(person) }}
              </option>
            </select>

            <button class="btn btn-start" :disabled="isBusy || !selectedPersonId" @click="assignSelectedCluster">
              {{ isBusy && activeAction === 'assign' ? t('people_review.saving') : t('people_review.assign_existing_button') }}
            </button>
          </section>

          <section class="people-review-action-card people-review-action-card-create">
            <h3 class="people-review-action-title">{{ t('people_review.create_person_title') }}</h3>
            <p class="people-review-action-text">{{ t('people_review.create_person_text') }}</p>

            <input
              v-model.trim="newPersonName"
              type="text"
              class="people-review-input"
              :placeholder="t('people_review.create_person_placeholder')"
              :disabled="isBusy"
            >

            <textarea
              v-model.trim="newPersonNotes"
              class="people-review-notes"
              :placeholder="t('people_review.notes_placeholder')"
              :disabled="isBusy"
            />

            <button class="btn btn-start" :disabled="isBusy || !newPersonName" @click="createPersonForCluster">
              {{ isBusy && activeAction === 'create' ? t('people_review.saving') : t('people_review.create_person_button') }}
            </button>
          </section>
        </div>

        <div class="people-review-faces-header">
          <h3 class="people-review-faces-title">{{ t('people_review.faces_title') }}</h3>
          <p class="people-review-faces-hint">{{ t('people_review.faces_hint') }}</p>
        </div>

        <div class="people-review-faces-grid">
          <article v-for="(face, index) in selectedCluster.faces" :key="face.id" class="people-review-face-card">
            <div class="people-review-face-thumb-wrap">
              <img v-if="face.thumb_url" :src="face.thumb_url" alt="" class="people-review-face-thumb">
              <div v-else class="people-review-face-thumb-fallback">{{ index + 1 }}</div>
              <span class="people-review-face-order">{{ index + 1 }}</span>
            </div>

            <div class="people-review-face-caption">
              <span class="people-review-face-name">{{ face.person?.name || t('people_review.unknown_face', { index: index + 1 }) }}</span>
              <span class="people-review-face-status" :class="face.person ? 'resolved' : 'pending'">
                {{ face.person ? t('people_review.status_resolved') : t('people_review.status_pending') }}
              </span>
              <span class="people-review-face-path" :title="face.file_path">{{ face.file_path }}</span>
            </div>

            <div class="people-review-face-actions">
              <button
                class="btn btn-danger"
                :disabled="isBusy"
                @click="excludeFace(face.id)"
              >
                {{ isBusy && activeAction === `exclude:${face.id}` ? t('people_review.saving') : t('people_review.exclude_face_button') }}
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../../api.js'
import { replaceForRouteFailure, ROUTE_LOAD_TIMEOUT_MS } from '../../routeErrors.js'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const clusters = ref([])
const people = ref([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')
const selectedClusterId = ref(null)
const selectedPersonId = ref('')
const newPersonName = ref('')
const newPersonNotes = ref('')
const activeAction = ref('')

const totalFaces = computed(() =>
  clusters.value.reduce((sum, cluster) => sum + cluster.face_count, 0)
)

const selectedCluster = computed(() =>
  clusters.value.find(cluster => cluster.id === selectedClusterId.value) ?? null
)

const isBusy = computed(() => activeAction.value !== '')

function personLabel(person) {
  if (person.name) return person.name
  return t('people_review.person_without_name', { id: person.id })
}

async function responseDetail(response, fallbackKey) {
  try {
    const data = await response.json()
    if (typeof data?.detail === 'string' && data.detail) return data.detail
  } catch {
    // Ignore invalid error payloads.
  }
  return t(fallbackKey)
}

async function loadReviewData({ fatal = false } = {}) {
  loading.value = true
  loadError.value = ''

  try {
    const [clustersRes, peopleRes] = await Promise.all([
      apiFetch('/people/review/clusters', { timeoutMs: ROUTE_LOAD_TIMEOUT_MS }),
      apiFetch('/people/review/persons', { timeoutMs: ROUTE_LOAD_TIMEOUT_MS }),
    ])

    if (!clustersRes.ok) {
      if (fatal) {
        await replaceForRouteFailure(router, route, clustersRes)
        return
      }
      loadError.value = await responseDetail(clustersRes, 'people_review.load_error')
      return
    }

    if (!peopleRes.ok) {
      if (fatal) {
        await replaceForRouteFailure(router, route, peopleRes)
        return
      }
      loadError.value = await responseDetail(peopleRes, 'people_review.load_error')
      return
    }

    clusters.value = await clustersRes.json()
    people.value = await peopleRes.json()
  } catch (error) {
    if (fatal) {
      await replaceForRouteFailure(router, route, error)
      return
    }
    loadError.value = t('people_review.load_error')
  } finally {
    loading.value = false
  }
}

async function runAction(actionKey, request) {
  actionError.value = ''
  activeAction.value = actionKey

  try {
    const response = await request()
    if (!response.ok) {
      actionError.value = await responseDetail(response, 'people_review.action_error')
      return false
    }

    await loadReviewData()
    return true
  } catch {
    actionError.value = t('people_review.action_error')
    return false
  } finally {
    activeAction.value = ''
  }
}

async function assignSelectedCluster() {
  if (!selectedCluster.value || !selectedPersonId.value) return

  const ok = await runAction('assign', () =>
    apiFetch(`/people/review/clusters/${selectedCluster.value.id}/assign`, {
      method: 'POST',
      body: { person_id: Number(selectedPersonId.value) },
    })
  )

  if (ok) selectedPersonId.value = ''
}

async function createPersonForCluster() {
  if (!selectedCluster.value || !newPersonName.value) return

  const ok = await runAction('create', () =>
    apiFetch(`/people/review/clusters/${selectedCluster.value.id}/create-person`, {
      method: 'POST',
      body: {
        name: newPersonName.value,
        notes: newPersonNotes.value || null,
      },
    })
  )

  if (ok) {
    newPersonName.value = ''
    newPersonNotes.value = ''
  }
}

async function excludeFace(faceId) {
  await runAction(`exclude:${faceId}`, () =>
    apiFetch(`/people/review/faces/${faceId}/exclude`, {
      method: 'POST',
    })
  )
}

watch(clusters, (nextClusters) => {
  if (nextClusters.length === 0) {
    selectedClusterId.value = null
    return
  }

  const stillExists = nextClusters.some(cluster => cluster.id === selectedClusterId.value)
  if (!stillExists) selectedClusterId.value = nextClusters[0].id
}, { immediate: true })

watch(selectedClusterId, () => {
  selectedPersonId.value = ''
  actionError.value = ''
})

onMounted(() => {
  void loadReviewData({ fatal: true })
})
</script>

<style scoped>
.people-review {
  min-height: 100%;
  padding: var(--sp-7);
  background:
    radial-gradient(circle at top right, rgba(212, 170, 106, 0.16), transparent 28%),
    linear-gradient(180deg, rgba(122, 163, 192, 0.08), transparent 22%),
    var(--bg);
}

.people-review-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--sp-5);
}

.people-review-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  justify-content: flex-end;
}

.people-review-summary-label,
.people-review-stat-pill,
.people-review-cluster-tag,
.people-review-empty-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: var(--inset-pill-y) var(--inset-pill-x);
  border-radius: var(--radius-pill);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.people-review-summary-label,
.people-review-stat-pill {
  background: var(--bg-accent);
  color: var(--accent);
  border: 1px solid var(--border-accent);
}

.people-review-layout {
  display: grid;
  grid-template-columns: minmax(18rem, 22rem) minmax(0, 1fr);
  gap: var(--sp-5);
}

.people-review-rail,
.people-review-detail,
.people-review-empty-card,
.people-review-action-card,
.people-review-face-card {
  background: color-mix(in srgb, var(--surface) 92%, white 8%);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-dialog);
}

.people-review-rail {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-3);
  max-height: calc(100vh - 13rem);
  overflow-y: auto;
}

.people-review-cluster {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-4);
  border: 1px solid transparent;
  border-radius: calc(var(--radius-lg) - 4px);
  background:
    linear-gradient(135deg, rgba(122, 163, 192, 0.08), rgba(212, 170, 106, 0.12)),
    var(--surface);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: transform var(--motion-base), border-color var(--motion-base), box-shadow var(--motion-base);
}

.people-review-cluster:hover {
  transform: translateY(-1px);
  border-color: var(--border-accent);
}

.people-review-cluster.active {
  border-color: var(--accent);
  box-shadow: var(--shadow-floating);
}

.people-review-cluster-header,
.people-review-cluster-footer,
.people-review-detail-header,
.people-review-faces-header,
.people-review-face-caption,
.people-review-face-actions {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-3);
}

.people-review-cluster-header,
.people-review-cluster-footer {
  align-items: center;
}

.people-review-cluster-tag,
.people-review-empty-badge {
  background: rgba(212, 170, 106, 0.14);
  color: #8b621e;
}

.people-review-cluster-meta,
.people-review-cluster-footer,
.people-review-detail-kicker,
.people-review-detail-text,
.people-review-action-text,
.people-review-faces-hint,
.people-review-face-path,
.people-review-empty-text,
.people-review-empty-loading {
  color: var(--text-muted);
}

.people-review-cluster-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--sp-2);
}

.people-review-cluster-strip-item,
.people-review-face-thumb-wrap {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-md);
  background: linear-gradient(160deg, rgba(122, 163, 192, 0.16), rgba(212, 170, 106, 0.16));
}

.people-review-cluster-strip-item {
  aspect-ratio: 4 / 5;
}

.people-review-cluster-strip-thumb,
.people-review-face-thumb {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.people-review-cluster-strip-fallback,
.people-review-face-thumb-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--text-muted);
  font-size: var(--fs-sm);
  font-weight: 600;
}

.people-review-detail {
  padding: var(--sp-5);
}

.people-review-detail-header {
  align-items: flex-start;
  margin-bottom: var(--sp-2);
}

.people-review-detail-kicker {
  margin: 0 0 var(--sp-1);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: var(--fs-2xs);
}

.people-review-detail-title,
.people-review-empty-title,
.people-review-action-title,
.people-review-faces-title {
  margin: 0;
  color: var(--text-heading);
}

.people-review-detail-title {
  font-size: 1.35rem;
}

.people-review-detail-text {
  margin: 0 0 var(--sp-5);
  max-width: 46rem;
  line-height: 1.6;
}

.people-review-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-4);
  margin-bottom: var(--sp-5);
}

.people-review-action-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-4);
}

.people-review-action-card-create {
  background:
    linear-gradient(180deg, rgba(212, 170, 106, 0.12), transparent 70%),
    var(--surface);
}

.people-review-action-text,
.people-review-faces-hint,
.people-review-empty-text {
  margin: 0;
  line-height: 1.55;
}

.people-review-select,
.people-review-input,
.people-review-notes {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  padding: var(--sp-3);
}

.people-review-notes {
  min-height: 6.5rem;
  resize: vertical;
}

.people-review-faces-header {
  align-items: end;
  margin-bottom: var(--sp-4);
}

.people-review-faces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: var(--sp-4);
}

.people-review-face-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-3);
}

.people-review-face-thumb-wrap {
  aspect-ratio: 4 / 5;
}

.people-review-face-order {
  position: absolute;
  top: var(--sp-2);
  left: var(--sp-2);
  min-width: 1.65rem;
  height: 1.65rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  background: rgba(15, 23, 42, 0.72);
  color: white;
  font-size: var(--fs-xs);
  font-weight: 700;
}

.people-review-face-caption {
  flex-direction: column;
}

.people-review-face-name {
  font-weight: 600;
  color: var(--text-heading);
}

.people-review-face-status {
  width: fit-content;
  font-size: var(--fs-xs);
  font-weight: 600;
  padding: var(--sp-1) var(--sp-2);
  border-radius: var(--radius-pill);
}

.people-review-face-status.pending {
  background: var(--bg-warning);
  color: #8b621e;
}

.people-review-face-status.resolved {
  background: var(--bg-success);
  color: var(--success);
}

.people-review-face-path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: monospace;
  font-size: var(--fs-xs);
}

.people-review-face-actions {
  justify-content: flex-start;
}

.people-review-empty {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.people-review-empty-card {
  max-width: 34rem;
  padding: var(--sp-7);
  text-align: center;
  background:
    radial-gradient(circle at top center, rgba(122, 163, 192, 0.14), transparent 55%),
    var(--surface);
}

.people-review-empty-title {
  margin-top: var(--sp-3);
  margin-bottom: var(--sp-2);
}

.people-review-action-error {
  margin-bottom: var(--sp-4);
}

@media (max-width: 1100px) {
  .people-review {
    padding: var(--sp-5);
  }

  .people-review-layout {
    grid-template-columns: 1fr;
  }

  .people-review-rail {
    max-height: none;
    overflow-x: auto;
    overflow-y: hidden;
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: minmax(16rem, 18rem);
  }
}

@media (max-width: 760px) {
  .people-review-actions {
    grid-template-columns: 1fr;
  }

  .people-review-hero,
  .people-review-detail-header,
  .people-review-faces-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .people-review-rail {
    grid-auto-columns: minmax(15rem, 82vw);
  }

  .people-review-empty-card,
  .people-review-detail {
    padding: var(--sp-5);
  }
}
</style>
