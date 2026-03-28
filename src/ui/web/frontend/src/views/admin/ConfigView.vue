<template>
  <h1 class="page-title">{{ t('admin.settings.title') }}</h1>
  <p class="page-subtitle">{{ t('admin.settings.subtitle') }}</p>

  <ConfirmDialog
    :visible="showConfirm"
    :title="t('admin.settings.confirm_archive_title')"
    :message="t('admin.settings.confirm_archive_message')"
    :confirmLabel="t('admin.settings.change_archive')"
    @confirm="onConfirm"
    @cancel="showConfirm = false"
  />

  <div class="config-body">

    <div class="field">
      <label class="field-label">{{ t('admin.settings.inbox') }}</label>
      <input class="field-input" v-model="form.inbox" :placeholder="t('admin.settings.inbox_placeholder')" />
      <div class="field-hint">{{ t('admin.settings.inbox_hint') }}</div>
    </div>
    <div class="field-actions">
      <button class="btn btn-save" @click="saveInbox" :disabled="savingInbox">
        {{ t('admin.settings.save') }}
      </button>
      <span class="saved-msg" v-if="savedInbox">{{ t('admin.settings.saved') }}</span>
      <span class="field-error-inline" v-if="inboxError">{{ inboxError }}</span>
    </div>

    <div class="field field-mt">
      <label class="field-label">
        {{ t('admin.settings.archive') }}
        <span class="label-warning">— {{ t('admin.settings.archive_hint') }}</span>
      </label>
      <input class="field-input" v-model="form.archive" :placeholder="t('admin.settings.archive_placeholder')" />
    </div>
    <div class="field-actions">
      <button class="btn btn-danger" @click="saveArchive" :disabled="savingArchive">
        {{ t('admin.settings.change_archive') }}
      </button>
      <span class="saved-msg" v-if="savedArchive">{{ t('admin.settings.saved') }}</span>
      <span class="field-error-inline" v-if="archiveError">{{ archiveError }}</span>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import ConfirmDialog from '../../components/ConfirmDialog.vue'
import { apiFetch } from '../../api.js'

const { t, te } = useI18n()
function translateError(code) {
  const key = 'setup.validation.' + code
  return te(key) ? t(key) : t('admin.settings.save_error')
}
const form = ref({ archive: '', inbox: '' })

const savingInbox = ref(false)
const savedInbox = ref(false)
const inboxError = ref('')

const savingArchive = ref(false)
const savedArchive = ref(false)
const archiveError = ref('')
const showConfirm = ref(false)

onMounted(async () => {
  const res = await apiFetch('/config')
  form.value = await res.json()
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
  if (!form.value.archive.trim()) { archiveError.value = t('setup.validation.required'); return }
  showConfirm.value = true
}

async function onConfirm() {
  showConfirm.value = false
  savingArchive.value = true
  savedArchive.value = false
  archiveError.value = ''
  try {
    const res = await apiFetch('/config/archive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archive: form.value.archive }),
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
