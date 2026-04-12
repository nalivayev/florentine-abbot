<template>
  <h1 class="page-title">{{ t('services.title') }}</h1>
  <p class="page-subtitle">{{ t('services.subtitle') }}</p>

  <div v-for="item in daemonItems" :key="item.key" class="service-section">
    <div class="service-header">
      <span class="service-label">{{ t(`services.${item.key}.label`) }}</span>
      <span class="badge" :class="`badge-${item.daemon?.status ?? 'stopped'}`">
        {{ t(`daemons.status.${item.daemon?.status ?? 'stopped'}`) }}
      </span>
    </div>
    <p class="service-desc">{{ t(`services.${item.key}.description`) }}</p>

    <div class="info-row" v-if="item.daemon?.watch_path">
      <span class="info-label">{{ t('daemons.watch') }}</span>
      <span class="info-value">{{ item.daemon.watch_path }}</span>
    </div>
    <div class="info-row" v-if="item.daemon?.output_path">
      <span class="info-label">{{ t('daemons.output') }}</span>
      <span class="info-value">{{ item.daemon.output_path }}</span>
    </div>

    <div class="service-actions">
      <button v-if="item.daemon?.status === 'running'"
        class="btn btn-stop" @click="stop(item.name)">{{ t('daemons.stop') }}</button>
      <button v-else-if="item.daemon?.status === 'crashed'"
        class="btn btn-retry" @click="start(item.name)">{{ t('daemons.restart') }}</button>
      <button v-else-if="item.daemon?.status === 'not_configured'"
        class="btn" disabled>{{ t('daemons.status.not_configured') }}</button>
      <button v-else
        class="btn btn-start" @click="start(item.name)">{{ t('daemons.start') }}</button>
      <button class="btn btn-log" @click="openLog(item)">{{ t('services.log') }}</button>
    </div>

    <p v-if="item.daemon?.status === 'not_configured'" class="not-configured-hint">
      <i18n-t keypath="daemons.not_configured_hint" tag="span">
        <template #link>
          <router-link to="/settings">{{ t('daemons.go_to_settings') }}</router-link>
        </template>
      </i18n-t>
    </p>

    <div class="error-block" v-if="item.daemon?.status === 'crashed' && item.daemon?.error">
      {{ item.daemon.error }}
    </div>
  </div>

  <div v-if="logItem" class="overlay" @click.self="closeLog">
    <div class="dialog log-dialog">
      <div class="log-dialog-header">
        <span class="dialog-title">{{ t(`services.${logItem.key}.label`) }}</span>
        <button class="btn-close" @click="closeLog">✕</button>
      </div>
      <div class="log-panel" ref="logPanel">
        <div v-if="logs.length === 0" class="log-empty">{{ t('daemons.no_logs') }}</div>
        <div v-for="(line, i) in logs" :key="i" class="log-line">{{ line }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiFetch, apiUrl } from '../api.js'

const { t } = useI18n()

const DAEMON_LIST = [
  { key: 'processor', name: 'preview-maker' },
  { key: 'tiler', name: 'tile-cutter' },
  { key: 'keeper', name: 'archive-keeper' },
]

const daemons = ref([])
const logItem = ref(null)
const logs = ref([])
const logPanel = ref(null)
let pollInterval = null
let eventSource = null

const daemonItems = computed(() =>
  DAEMON_LIST.map(item => ({
    ...item,
    daemon: daemons.value.find(d => d.descriptor.name === item.name),
  }))
)

async function fetchDaemons() {
  const res = await apiFetch('/daemons')
  daemons.value = await res.json()
}

async function start(name) {
  await apiFetch(`/daemons/${name}/start`, { method: 'POST' })
  await fetchDaemons()
}

async function stop(name) {
  await apiFetch(`/daemons/${name}/stop`, { method: 'POST' })
  await fetchDaemons()
}

function openLog(item) {
  logItem.value = item
  logs.value = []
  if (eventSource) eventSource.close()
  const token = localStorage.getItem('token')
  eventSource = new EventSource(apiUrl(`/daemons/${item.name}/logs?token=${token}`))
  eventSource.onmessage = async (e) => {
    logs.value.push(JSON.parse(e.data))
    await nextTick()
    if (logPanel.value) logPanel.value.scrollTop = logPanel.value.scrollHeight
  }
}

function closeLog() {
  logItem.value = null
  logs.value = []
  if (eventSource) { eventSource.close(); eventSource = null }
}

onMounted(() => {
  fetchDaemons()
  pollInterval = setInterval(fetchDaemons, 5000)
})

onUnmounted(() => {
  clearInterval(pollInterval)
  if (eventSource) eventSource.close()
})
</script>

<style scoped>
.service-section {
  padding: var(--sp-5) 0;
  border-bottom: 1px solid var(--border);
}
.service-section:last-child { border-bottom: none; }
.service-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
}
.service-label {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text);
}
.service-desc {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  margin: 0 0 var(--sp-3);
}
.service-actions {
  display: flex;
  gap: var(--sp-2);
  margin-top: var(--sp-4);
}
.btn-log {
  background: var(--surface);
  color: var(--text-muted);
  border-color: var(--border);
}
.btn-log:hover { color: var(--text); border-color: var(--text-muted); }
.log-dialog {
  width: 680px;
  max-width: calc(100vw - 2rem);
}
.log-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-4);
}
.btn-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: var(--fs-base);
  padding: 0;
  line-height: 1;
}
.btn-close:hover { color: var(--text); }
</style>
