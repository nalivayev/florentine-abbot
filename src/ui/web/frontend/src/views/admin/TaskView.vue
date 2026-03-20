<template>
  <div v-if="daemon">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
      <h1 class="page-title">{{ t(`tasks.${route.params.task}.label`) }}</h1>
      <span class="badge" :class="`badge-${daemon.status}`">{{ statusLabel }}</span>
    </div>
    <p class="page-subtitle">{{ t(`tasks.${route.params.task}.description`) }}</p>

    <div class="info-row" v-if="daemon.watch_path">
      <span class="info-label">{{ t('daemons.watch') }}</span>
      <span class="info-value">{{ daemon.watch_path }}</span>
    </div>
    <div class="info-row" v-if="daemon.output_path">
      <span class="info-label">{{ t('daemons.output') }}</span>
      <span class="info-value">{{ daemon.output_path }}</span>
    </div>

    <div style="margin-top: 24px;">
      <button v-if="daemon.status === 'running'"
        class="btn btn-stop" @click="stop">{{ t('daemons.stop') }}</button>
      <button v-else-if="daemon.status === 'crashed'"
        class="btn btn-retry" @click="start">Retry</button>
      <button v-else-if="daemon.status === 'not_configured'"
        class="btn" disabled>Not configured</button>
      <button v-else
        class="btn btn-start" @click="start">{{ t('daemons.start') }}</button>
    </div>

    <div class="error-block" v-if="daemon.status === 'crashed' && daemon.error">{{ daemon.error }}</div>

    <hr class="divider">
    <div class="log-header">Вывод</div>
    <div class="log-panel" ref="logPanel">
      <div v-if="logs.length === 0" class="log-empty">{{ t('daemons.no_logs') }}</div>
      <div v-for="(line, i) in logs" :key="i" class="log-line">{{ line }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiFetch, apiUrl } from '../../api.js'

const { t } = useI18n()

const DAEMON_NAMES = {
  organizer: 'file-organizer',
  processor: 'preview-maker',
  detector: 'face-detector',
}

const route = useRoute()
const daemons = ref([])
const logs = ref([])
const logPanel = ref(null)
let pollInterval = null
let eventSource = null

const daemonName = computed(() => DAEMON_NAMES[route.params.task])
const daemon = computed(() => daemons.value.find(d => d.descriptor.name === daemonName.value))
const statusLabel = computed(() => t(`daemons.status.${daemon.value?.status}`) ?? '')

async function fetchDaemons() {
  const res = await apiFetch('/daemons')
  daemons.value = await res.json()
}

async function start() {
  await apiFetch(`/daemons/${daemonName.value}/start`, { method: 'POST' })
  await fetchDaemons()
}

async function stop() {
  await apiFetch(`/daemons/${daemonName.value}/stop`, { method: 'POST' })
  await fetchDaemons()
}

function connectLogs(name) {
  if (eventSource) eventSource.close()
  logs.value = []
  const token = localStorage.getItem('token')
  eventSource = new EventSource(apiUrl(`/daemons/${name}/logs?token=${token}`))
  eventSource.onmessage = async (e) => {
    logs.value.push(JSON.parse(e.data))
    await nextTick()
    if (logPanel.value) logPanel.value.scrollTop = logPanel.value.scrollHeight
  }
}

watch(daemonName, (name) => { if (name) connectLogs(name) })

onMounted(() => {
  fetchDaemons()
  pollInterval = setInterval(fetchDaemons, 5000)
  if (daemonName.value) connectLogs(daemonName.value)
})

onUnmounted(() => {
  clearInterval(pollInterval)
  if (eventSource) eventSource.close()
})
</script>
