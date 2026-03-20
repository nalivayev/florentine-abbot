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

  <div style="max-width: 480px;">

    <div class="field">
      <label class="field-label">{{ t('settings.inbox') }}</label>
      <input class="field-input" v-model="form.inbox" placeholder="/path/to/inbox" />
      <div class="field-hint">{{ t('settings.inbox_hint') }}</div>
    </div>
    <div class="field-actions">
      <button class="btn btn-save" @click="saveInbox" :disabled="savingInbox">
        {{ t('settings.save') }}
      </button>
      <span class="saved-msg" v-if="savedInbox">{{ t('settings.saved') }}</span>
      <span class="field-error-inline" v-if="inboxError">{{ inboxError }}</span>
    </div>

    <div class="field" style="margin-top: 32px;">
      <label class="field-label">
        {{ t('settings.archive') }}
        <span class="label-warning">— {{ t('settings.archive_hint') }}</span>
      </label>
      <input class="field-input" v-model="form.archive" placeholder="/path/to/archive" />
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
import ConfirmDialog from '../../components/ConfirmDialog.vue'
import { apiFetch } from '../../api.js'

const { t } = useI18n()
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
  if (!form.value.inbox.trim()) { inboxError.value = t('settings.inbox'); return }
  savingInbox.value = true
  savedInbox.value = false
  inboxError.value = ''
  try {
    const res = await apiFetch('/config/inbox', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inbox: form.value.inbox }),
    })
    if (!res.ok) inboxError.value = (await res.json()).detail || 'Ошибка'
    else { savedInbox.value = true; setTimeout(() => savedInbox.value = false, 3000) }
  } finally { savingInbox.value = false }
}

function saveArchive() {
  if (!form.value.archive.trim()) { archiveError.value = t('settings.archive'); return }
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
    if (!res.ok) archiveError.value = (await res.json()).detail || 'Ошибка'
    else { savedArchive.value = true; setTimeout(() => savedArchive.value = false, 3000) }
  } finally { savingArchive.value = false }
}
</script>
