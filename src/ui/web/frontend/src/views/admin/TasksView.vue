<template>
  <h1 class="page-title">{{ t('tasks.title') }}</h1>
  <p class="page-subtitle">{{ t('tasks.subtitle') }}</p>

  <div v-if="loading" class="state-msg">{{ t('tasks.loading') }}</div>
  <div v-else-if="!items.length" class="state-msg">{{ t('tasks.empty') }}</div>
  <template v-else>
    <table class="tasks-table">
      <thead>
        <tr>
          <th>{{ t('tasks.col_task') }}</th>
          <th>{{ t('tasks.col_status') }}</th>
          <th>{{ t('tasks.col_progress') }}</th>
          <th>{{ t('tasks.col_created') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in items" :key="task.id">
          <td class="task-type">{{ task.domain }} / {{ task.action }}</td>
          <td>
            <span class="badge" :class="`badge-task-${task.status}`">
              {{ t(`tasks.status.${task.status}`, task.status) }}
            </span>
          </td>
          <td class="task-progress">
            <template v-if="task.steps > 0">
              <span>{{ task.done }}/{{ task.steps }}</span>
              <span v-if="task.failed > 0" class="failed-count">
                &nbsp;({{ t('tasks.failed_count', { count: task.failed }) }})
              </span>
            </template>
            <span v-else class="text-muted">—</span>
          </td>
          <td class="task-date">{{ formatDate(task.created_at) }}</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button class="btn btn-page" :disabled="page <= 1" @click="goTo(page - 1)">&#8249;</button>
      <span class="page-info">{{ t('tasks.page_of', { page, pages }) }}</span>
      <button class="btn btn-page" :disabled="page >= pages" @click="goTo(page + 1)">&#8250;</button>
    </div>
  </template>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../../api.js'
import { replaceForRouteFailure, ROUTE_LOAD_TIMEOUT_MS } from '../../routeErrors.js'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const loading = ref(true)

let pollInterval = null

const hasActive = computed(() =>
  items.value.some(task => task.status === 'running' || task.status === 'pending')
)

async function load({ fatal = false } = {}) {
  try {
    const res = await apiFetch(`/tasks?page=${page.value}&per_page=25`, {
      timeoutMs: ROUTE_LOAD_TIMEOUT_MS,
    })
    if (!res.ok) {
      if (fatal) await replaceForRouteFailure(router, route, res)
      return
    }
    const data = await res.json()
    items.value = data.items
    total.value = data.total
    pages.value = data.pages
  } catch (err) {
    if (fatal) await replaceForRouteFailure(router, route, err)
  } finally {
    loading.value = false
  }
}

async function goTo(p) {
  page.value = p
  loading.value = true
  await load()
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(locale.value, { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(() => {
  void load({ fatal: true })
  pollInterval = setInterval(() => {
    if (hasActive.value) void load()
  }, 5000)
})

onUnmounted(() => clearInterval(pollInterval))
</script>

<style scoped>
.state-msg {
  color: var(--text-muted);
  padding: var(--sp-6) 0;
}
.tasks-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm);
  margin-top: var(--sp-4);
}
.tasks-table th {
  text-align: left;
  color: var(--text-muted);
  font-weight: 500;
  padding: var(--sp-2) var(--sp-4) var(--sp-2) 0;
  border-bottom: 1px solid var(--border);
}
.tasks-table td {
  padding: var(--sp-3) var(--sp-4) var(--sp-3) 0;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.tasks-table tr:last-child td { border-bottom: none; }
.task-type {
  font-family: monospace;
  color: var(--text);
}
.task-date {
  color: var(--text-muted);
  white-space: nowrap;
}
.task-progress { white-space: nowrap; }
.failed-count { color: var(--danger); }
.text-muted { color: var(--text-muted); }
.pagination {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-top: var(--sp-5);
}
.btn-page {
  min-width: 2rem;
  padding: var(--sp-1) var(--sp-2);
}
.page-info {
  font-size: var(--fs-sm);
  color: var(--text-muted);
}
</style>
