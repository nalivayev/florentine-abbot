<template>
  <h1 class="page-title">{{ t('settings.title') }}</h1>
  <p class="page-subtitle">{{ t('settings.subtitle') }}</p>

  <ConfirmDialog
    :visible="showConfirm"
    :title="t('settings.confirm_archive_title')"
    :message="t('settings.confirm_archive_message')"
    :confirmLabel="t('settings.change_archive')"
    @confirm="onConfirm"
    @cancel="showConfirm = false"
  />

  <div class="config-body">

    <div class="field">
      <label class="field-label">{{ t('settings.inbox') }}</label>
      <input class="field-input" v-model="form.inbox" :placeholder="t('settings.inbox_placeholder')" />
      <div class="field-hint">{{ t('settings.inbox_hint') }}</div>
    </div>
    <div class="field-actions">
      <button class="btn btn-save" @click="saveInbox" :disabled="savingInbox">
        {{ t('settings.save') }}
      </button>
      <span class="saved-msg" v-if="savedInbox">{{ t('settings.saved') }}</span>
      <span class="field-error-inline" v-if="inboxError">{{ inboxError }}</span>
    </div>

    <div class="field field-mt">
      <label class="field-label">
        {{ t('settings.archive') }}
        <span class="label-warning">— {{ t('settings.archive_hint') }}</span>
      </label>
      <input class="field-input" v-model="form.archive_path" :placeholder="t('settings.archive_placeholder')" />
    </div>
    <div class="field-actions">
      <button class="btn btn-danger" @click="saveArchive" :disabled="savingArchive">
        {{ t('settings.change_archive') }}
      </button>
      <span class="saved-msg" v-if="savedArchive">{{ t('settings.saved') }}</span>
      <span class="field-error-inline" v-if="archiveError">{{ archiveError }}</span>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { apiFetch } from '../api.js'
import { replaceForRouteFailure, ROUTE_LOAD_TIMEOUT_MS } from '../routeErrors.js'

const { t, te } = useI18n()
const route = useRoute()
const router = useRouter()
function translateError(code) {
  const key = 'setup.validation.' + code
  return te(key) ? t(key) : t('settings.save_error')
}
const form = ref({ archive_path: '', inbox: '' })

const savingInbox = ref(false)
const savedInbox = ref(false)
const inboxError = ref('')

const savingArchive = ref(false)
const savedArchive = ref(false)
const archiveError = ref('')
const showConfirm = ref(false)

onMounted(async () => {
  try {
    const res = await apiFetch('/config', { timeoutMs: ROUTE_LOAD_TIMEOUT_MS })
    if (!res.ok) {
      await replaceForRouteFailure(router, route, res)
      return
    }

    const data = await res.json()
    form.value = {
      archive_path: data.archive_path || '',
      inbox: data.inbox || '',
    }
  } catch (error) {
    await replaceForRouteFailure(router, route, error)
  }
})

async function saveInbox() {
  if (!form.value.inbox.trim()) { inboxError.value = t('setup.validation.required'); return }
  savingInbox.value = true
  savedInbox.value = false
  inboxError.value = ''
  try {
    const res = await apiFetch('/config/inbox', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inbox: form.value.inbox }),
    })
    if (!res.ok) inboxError.value = translateError((await res.json()).detail)
    else { savedInbox.value = true; setTimeout(() => savedInbox.value = false, 3000) }
  } finally { savingInbox.value = false }
}

function saveArchive() {
  if (!form.value.archive_path.trim()) { archiveError.value = t('setup.validation.required'); return }
  showConfirm.value = true
}

async function onConfirm() {
  showConfirm.value = false
  savingArchive.value = true
  savedArchive.value = false
  archiveError.value = ''
  try {
    const res = await apiFetch('/config/archive-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archive_path: form.value.archive_path }),
    })
    if (!res.ok) archiveError.value = translateError((await res.json()).detail)
    else { savedArchive.value = true; setTimeout(() => savedArchive.value = false, 3000) }
  } finally { savingArchive.value = false }
}
</script>

<style scoped>
.config-body { max-width: 480px; }
.field-mt { margin-top: var(--sp-7); }
</style>
