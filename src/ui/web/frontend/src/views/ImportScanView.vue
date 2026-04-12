<template>
  <h1 class="page-title">{{ t('import.scans.title') }}</h1>
  <p class="page-subtitle">{{ t('import.scans.subtitle') }}</p>

  <!-- Step: Intro -->
  <div v-if="step === 'intro'" class="step-content">
    <p class="intro-text">{{ t('import.scans.intro') }}</p>

    <p class="intro-section-title">{{ t('import.scans.requires_title') }}</p>
    <ul class="intro-list">
      <li>{{ t('import.scans.req_naming') }}</li>
      <li>{{ t('import.scans.req_extensions') }}</li>
      <li>{{ t('import.scans.req_ids') }}</li>
    </ul>

    <p class="intro-section-title">{{ t('import.scans.writes_title') }}</p>
    <ul class="intro-list">
      <li>{{ t('import.scans.write_identifier') }}</li>
      <li>{{ t('import.scans.write_date') }}</li>
      <li>{{ t('import.scans.write_history') }}</li>
      <li>{{ t('import.scans.write_instance') }}</li>
    </ul>
  </div>

  <!-- Step: Collection -->
  <div v-if="step === 'collection'" class="step-content">
    <div class="radio-group" style="margin-bottom: var(--sp-5);">
      <label class="radio-label">
        <input type="radio" v-model="collectionMode" value="existing" />
        {{ t('import.scans.collection_existing') }}
      </label>
      <label class="radio-label">
        <input type="radio" v-model="collectionMode" value="new" />
        {{ t('import.scans.collection_new') }}
      </label>
    </div>

    <div v-if="collectionMode === 'existing'">
      <div v-if="collections.length === 0" class="hint-text">
        {{ t('import.scans.collection_none') }}
      </div>
      <div v-else class="collection-list">
        <label
          v-for="c in collections"
          :key="c.id"
          class="collection-item"
          :class="{ selected: selectedCollectionId === c.id }"
          @click="selectedCollectionId = c.id"
        >
          <span class="collection-id">{{ String(c.id).padStart(6, '0') }}</span>
          <span class="collection-name">{{ c.name }}</span>
          <span class="collection-type">{{ c.type }}</span>
        </label>
      </div>
    </div>

    <div v-if="collectionMode === 'new'" class="field">
      <label class="field-label">{{ t('import.scans.collection_name') }}</label>
      <input
        class="field-input"
        v-model="newCollectionName"
        :placeholder="t('import.scans.collection_name_placeholder')"
      />
    </div>

    <span class="field-error-inline" v-if="collectionError">{{ collectionError }}</span>
  </div>

  <!-- Step: Source -->
  <div v-if="step === 'source'" class="step-content">
    <div class="field">
      <label class="field-label">{{ t('import.scans.source_path') }}</label>
      <input class="field-input" v-model="sourcePath" :placeholder="t('import.scans.source_path_placeholder')" />
    </div>

    <div class="field">
      <label class="field-label">{{ t('import.scans.transfer_mode') }}</label>
      <div class="radio-group">
        <label class="radio-label">
          <input type="radio" v-model="transferMode" value="copy" /> {{ t('import.scans.copy') }}
        </label>
        <label class="radio-label">
          <input type="radio" v-model="transferMode" value="move" /> {{ t('import.scans.move') }}
        </label>
      </div>
    </div>

    <div class="field">
      <label class="radio-label">
        <input type="checkbox" v-model="recursive" /> {{ t('import.scans.recursive') }}
      </label>
    </div>
  </div>

  <!-- Step: Format -->
  <div v-if="step === 'format'" class="step-content">
    <p class="intro-text">{{ t('import.scans.format_hint') }}</p>

    <div class="format-row">
      <span class="format-label">{{ t('setup.steps.format.path_label') }}</span>
      <code class="format-value"><span class="format-prefix">scan/{{ collectionIdFormatted }}/</span>{{ archivePathTemplate }}</code>
      <button class="btn-edit" @click="dialogOpen = 'path'">{{ t('setup.steps.format.edit') }}</button>
    </div>
    <div class="format-row">
      <span class="format-label">{{ t('setup.steps.format.filename_label') }}</span>
      <code class="format-value">{{ archiveFilenameTemplate }}</code>
      <button class="btn-edit" @click="dialogOpen = 'filename'">{{ t('setup.steps.format.edit') }}</button>
    </div>
  </div>

  <!-- Step: Preview -->
  <div v-if="step === 'preview'" class="step-content">
    <div class="summary-bar">
      <span class="summary-stat summary-ok">{{ t('import.scans.summary_ok', { n: summary.ok }) }}</span>
      <span class="summary-stat summary-skip">{{ t('import.scans.summary_skip', { n: summary.skipped }) }}</span>
    </div>

    <div class="file-table">
      <div class="file-table-head">
        <span>{{ t('import.scans.col_file') }}</span>
        <span>{{ t('import.scans.col_status') }}</span>
      </div>
      <div v-for="f in previewFiles" :key="f.path" class="file-row" :class="'row-' + f.status">
        <span class="file-name">{{ f.filename }}</span>
        <span :class="'status-' + f.status" :title="f.errors.join('; ')">{{ t('import.scans.status_' + f.status) }}</span>
      </div>
    </div>

    <span class="field-error-inline" v-if="importError">{{ importError }}</span>
  </div>

  <!-- Step: Done -->
  <div v-if="step === 'done'" class="step-content">
    <p class="summary-stat summary-ok" style="font-size: var(--fs-base); margin-bottom: var(--sp-2);">
      {{ t('import.scans.done_ok', { n: importResult.succeeded }) }}
    </p>
    <p v-if="importResult.failed > 0" class="summary-stat" style="color: var(--danger); margin-bottom: var(--sp-2);">
      {{ t('import.scans.done_failed', { n: importResult.failed }) }}
    </p>
  </div>

  <!-- Wizard nav -->
  <div class="wizard-nav">
    <button v-if="step !== 'done'" class="btn-back" @click="goBack" :disabled="previewing || importing">
      {{ t('setup.back') }}
    </button>
    <span v-else></span>

    <button v-if="step === 'intro'" class="btn-next" @click="step = 'collection'">
      {{ t('setup.next') }}
    </button>
    <button v-else-if="step === 'collection'" class="btn-next" @click="goToSource" :disabled="creatingCollection">
      {{ creatingCollection ? t('import.scans.collection_creating') : t('setup.next') }}
    </button>
    <button v-else-if="step === 'source'" class="btn-next" @click="goToFormat" :disabled="!sourcePath.trim()">
      {{ t('setup.next') }}
    </button>
    <button v-else-if="step === 'format'" class="btn-next" @click="runPreview" :disabled="previewing">
      {{ previewing ? t('import.scans.scanning') : t('import.scans.preview_btn') }}
    </button>
    <button v-else-if="step === 'preview'" class="btn-next" @click="startImport" :disabled="summary.ok === 0 || importing">
      {{ importing ? t('import.scans.importing') : t('import.scans.import_btn', { n: summary.ok }) }}
    </button>
    <button v-else-if="step === 'done'" class="btn-next" @click="reset">
      {{ t('import.scans.import_more') }}
    </button>
  </div>

  <span class="field-error-inline" v-if="step === 'source' && previewError">{{ previewError }}</span>

  <!-- Format dialogs -->
  <FormatEditDialog
    v-if="dialogOpen === 'path'"
    v-model="archivePathTemplate"
    :prefix="`scan/${collectionIdFormatted}/`"
    :title="t('setup.steps.format.dialog_title_path')"
    :hint="t('setup.steps.format.dialog_hint_path')"
    @close="dialogOpen = null"
  />
  <FormatEditDialog
    v-if="dialogOpen === 'filename'"
    v-model="archiveFilenameTemplate"
    :title="t('setup.steps.format.dialog_title_filename')"
    :hint="t('setup.steps.format.dialog_hint_filename')"
    @close="dialogOpen = null"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api.js'
import FormatEditDialog from '../components/FormatEditDialog.vue'

const { t } = useI18n()
const router = useRouter()

const STEPS = ['intro', 'collection', 'source', 'format', 'preview', 'done']

const step = ref('intro')
const sourcePath = ref('')
const transferMode = ref('copy')
const recursive = ref(false)

// Collection
const collections = ref([])
const collectionMode = ref('existing')
const selectedCollectionId = ref(null)
const newCollectionName = ref('')
const collectionError = ref('')
const creatingCollection = ref(false)

const collectionIdFormatted = computed(() =>
  selectedCollectionId.value ? String(selectedCollectionId.value).padStart(6, '0') : '000000'
)

const archivePathTemplate = ref('')
const archiveFilenameTemplate = ref('')
const dialogOpen = ref(null)

const previewing = ref(false)
const previewError = ref('')
const previewFiles = ref([])
const summary = ref({ total: 0, ok: 0, skipped: 0 })

const importing = ref(false)
const importError = ref('')
const importResult = ref({ succeeded: 0, failed: 0 })

onMounted(async () => {
  try {
    const res = await apiFetch('/config/format')
    const data = await res.json()
    archivePathTemplate.value = data.archive_path_template
    archiveFilenameTemplate.value = data.archive_filename_template
  } catch {
    archivePathTemplate.value = '{year:04d}/{year:04d}.{month:02d}.{day:02d}'
    archiveFilenameTemplate.value = '{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}'
  }

  try {
    const res = await apiFetch('/collections')
    collections.value = await res.json()
    if (collections.value.length > 0) {
      selectedCollectionId.value = collections.value[0].id
    } else {
      collectionMode.value = 'new'
    }
  } catch {
    collectionMode.value = 'new'
  }
})

function goBack() {
  const idx = STEPS.indexOf(step.value)
  if (idx <= 0) {
    router.push('/import')
  } else {
    step.value = STEPS[idx - 1]
  }
}

async function goToSource() {
  collectionError.value = ''

  if (collectionMode.value === 'existing') {
    if (!selectedCollectionId.value) {
      collectionError.value = t('import.scans.collection_select_required')
      return
    }
    step.value = 'source'
    return
  }

  // Create new collection
  if (!newCollectionName.value.trim()) {
    collectionError.value = t('import.scans.collection_name_required')
    return
  }

  creatingCollection.value = true
  try {
    const res = await apiFetch('/collections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'scan', name: newCollectionName.value.trim() }),
    })
    if (!res.ok) {
      const d = await res.json()
      collectionError.value = d.detail || t('import.scans.collection_create_error')
      return
    }
    const created = await res.json()
    collections.value.push(created)
    selectedCollectionId.value = created.id
    step.value = 'source'
  } catch {
    collectionError.value = t('import.scans.collection_create_error')
  } finally {
    creatingCollection.value = false
  }
}

async function goToFormat() {
  step.value = 'format'
}

function reset() {
  step.value = 'intro'
  sourcePath.value = ''
  newCollectionName.value = ''
  collectionError.value = ''
  previewFiles.value = []
  summary.value = { total: 0, ok: 0, skipped: 0 }
  importResult.value = { succeeded: 0, failed: 0 }
  previewError.value = ''
  importError.value = ''
}

async function runPreview() {
  if (!sourcePath.value.trim()) return
  previewing.value = true
  previewError.value = ''

  try {
    await apiFetch('/config/format', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        archive_path_template: archivePathTemplate.value,
        archive_filename_template: archiveFilenameTemplate.value,
      }),
    })
  } catch {
    // Non-fatal
  }

  try {
    const res = await apiFetch('/import/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: sourcePath.value,
        recursive: recursive.value,
        collection_id: selectedCollectionId.value,
        collection_type: 'scan',
      }),
    })
    if (!res.ok) {
      const d = await res.json()
      previewError.value = d.detail || t('import.scans.error_scan')
      step.value = 'source'
      return
    }
    const data = await res.json()
    previewFiles.value = data.files
    summary.value = data.summary
    step.value = 'preview'
  } catch {
    previewError.value = t('import.scans.error_scan')
    step.value = 'source'
  } finally {
    previewing.value = false
  }
}

async function startImport() {
  importing.value = true
  importError.value = ''
  try {
    const res = await apiFetch('/import/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: sourcePath.value,
        recursive: recursive.value,
        mode: transferMode.value,
        collection_id: selectedCollectionId.value,
        collection_type: 'scan',
      }),
    })
    if (!res.ok) {
      const d = await res.json()
      importError.value = d.detail || t('import.scans.error_import')
    } else {
      const data = await res.json()
      importResult.value = { succeeded: data.succeeded, failed: data.failed }
      step.value = 'done'
    }
  } catch {
    importError.value = t('import.scans.error_import')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.step-content {
  max-width: 560px;
  margin-bottom: var(--sp-6);
}
.intro-text {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  margin-bottom: var(--sp-4);
  line-height: 1.6;
}
.intro-section-title {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: var(--sp-4) 0 var(--sp-2);
}
.intro-list {
  margin: 0 0 var(--sp-2) var(--sp-5);
  padding: 0;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  line-height: 1.8;
}
.hint-text {
  font-size: var(--fs-sm);
  color: var(--text-muted);
}
.collection-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  margin-top: var(--sp-2);
}
.collection-item {
  display: grid;
  grid-template-columns: 5rem 1fr auto;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  font-size: var(--fs-sm);
  transition: border-color 0.15s;
}
.collection-item:hover { border-color: var(--accent); }
.collection-item.selected { border-color: var(--accent); background: var(--surface-muted); }
.collection-id { font-family: monospace; font-size: var(--fs-xs); color: var(--text-muted); }
.collection-name { color: var(--text); font-weight: 500; }
.collection-type { font-size: var(--fs-xs); color: var(--text-muted); }
.format-row {
  display: grid;
  grid-template-columns: 10rem 1fr auto;
  align-items: baseline;
  gap: var(--sp-3);
  padding: var(--sp-3) 0;
  border-bottom: 1px solid var(--border);
  font-size: var(--fs-sm);
}
.format-label { color: var(--text-muted); white-space: nowrap; }
.format-prefix { color: var(--text-muted); }
.format-value {
  font-family: monospace;
  font-size: var(--fs-xs);
  color: var(--text);
  word-break: break-all;
}
.btn-edit {
  background: none;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: var(--sp-1) var(--sp-3);
  font-size: var(--fs-sm);
  color: var(--text-muted);
  cursor: pointer;
  white-space: nowrap;
}
.btn-edit:hover { border-color: var(--accent); color: var(--accent); }
.summary-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
  font-size: var(--fs-sm);
}
.summary-stat { font-weight: 500; }
.summary-ok { color: var(--success); }
.summary-skip { color: var(--text-muted); }
.file-table {
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  max-height: 420px;
  overflow-y: auto;
}
.file-table-head {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--sp-4);
  padding: var(--sp-2) var(--sp-4);
  background: var(--surface-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}
.file-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--sp-4);
  align-items: center;
  padding: var(--sp-2) var(--sp-4);
  border-bottom: 1px solid var(--border);
  font-size: var(--fs-sm);
}
.file-row:last-child { border-bottom: none; }
.file-name {
  font-family: monospace;
  font-size: var(--fs-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.status-ok { color: var(--success); white-space: nowrap; }
.status-invalid { color: var(--danger); white-space: nowrap; }
.radio-group { display: flex; gap: var(--sp-5); margin-top: var(--sp-1); }
.radio-label { display: flex; align-items: center; gap: var(--sp-2); font-size: var(--fs-sm); cursor: pointer; }
</style>
