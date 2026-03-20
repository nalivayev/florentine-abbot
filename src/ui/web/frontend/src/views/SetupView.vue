<template>
  <div class="setup-wrap">
    <div class="setup-box">

      <!-- Sidebar -->
      <nav class="setup-sidebar">
        <div v-for="s in stepLabels" :key="s.n" :class="['step-item', stepState(s)]">
          <span class="step-icon">{{ stepIcon(s) }}</span>
          <span class="step-label">{{ s.label }}</span>
        </div>
      </nav>

      <!-- Main -->
      <div class="setup-main">
        <!-- Language switcher -->
        <div class="lang-bar">
          <button v-for="lang in ['ru', 'en']" :key="lang"
            :class="['lang-btn', { active: locale === lang }]"
            @click="locale = lang; saveLang(lang)">{{ lang.toUpperCase() }}</button>
        </div>

        <div class="setup-content">

      <!-- Step 1: Account + Archive -->
      <section v-if="step === 1">
        <h1>{{ t('setup.steps.archive.label') }}</h1>
        <p class="hint">{{ t('setup.steps.archive.hint') }}</p>

        <div class="field">
          <label>{{ t('setup.archive_path') }}</label>
          <input v-model="archive" type="text" placeholder="C:\archive" :class="{ invalid: fieldErrors.archive }" />
          <p class="field-hint" :class="{ 'field-hint-error': fieldErrors.archive }">{{ t('setup.steps.archive.archive_path_hint') }}</p>
        </div>
        <div class="field">
          <label>{{ t('setup.username') }}</label>
          <input v-model="username" type="text" autocomplete="username" :class="{ invalid: fieldErrors.username }" />
          <p class="field-hint" :class="{ 'field-hint-error': fieldErrors.username }">{{ t('setup.steps.archive.username_hint') }}</p>
        </div>
        <div class="field">
          <label>{{ t('setup.password') }}</label>
          <input v-model="password" type="password" autocomplete="new-password" :class="{ invalid: fieldErrors.password }" />
          <p class="field-hint" :class="{ 'field-hint-error': fieldErrors.password }">{{ t('setup.steps.archive.password_hint') }}</p>
        </div>
        <div class="field">
          <label>{{ t('setup.password_confirm') }}</label>
          <input v-model="password2" type="password" autocomplete="new-password" :class="{ invalid: fieldErrors.password2 }" />
          <p class="field-hint" :class="{ 'field-hint-error': fieldErrors.password2 }">{{ t('setup.steps.archive.password_confirm_hint') }}</p>
        </div>
      </section>

      <!-- Step 2: Existing photos? -->
      <section v-else-if="step === 2">
        <h1>{{ t('setup.steps.existing.label') }}</h1>
        <p class="hint">{{ t('setup.steps.existing.hint') }}</p>

        <div class="choice">
          <button type="button" :class="['choice-btn', { selected: hasExisting === true }]"
            @click="hasExisting = true; fieldErrors = {}">{{ t('setup.steps.existing.yes') }}</button>
          <button type="button" :class="['choice-btn', { selected: hasExisting === false }]"
            @click="hasExisting = false; fieldErrors = {}">{{ t('setup.steps.existing.no') }}</button>
        </div>
        <p v-if="fieldErrors.choice" class="field-error">{{ t('setup.validation.' + fieldErrors.choice) }}</p>
      </section>

      <!-- Step 3: Import settings (only if hasExisting) -->
      <section v-else-if="step === 3">
        <h1>{{ t('setup.steps.import.label') }}</h1>
        <p class="hint">{{ t('setup.steps.import.hint') }}</p>

        <div class="field">
          <label>{{ t('setup.steps.import.input_path') }}</label>
          <input v-model="importPath" type="text" placeholder="C:\photos" :class="{ invalid: fieldErrors.import_path }" />
          <p v-if="fieldErrors.import_path" class="field-hint field-hint-error">{{ t('setup.validation.' + fieldErrors.import_path) }}</p>
        </div>
        <div class="field checkbox">
          <input id="recursive" v-model="importRecursive" type="checkbox" />
          <label for="recursive">{{ t('setup.steps.import.recursive') }}</label>
        </div>
      </section>

      <!-- Step 4: Preview dry-run (only if hasExisting) -->
      <section v-else-if="step === 4">
        <h1>{{ t('setup.steps.preview.label') }}</h1>
        <p class="hint">{{ t('setup.steps.preview.hint') }}</p>

        <div v-if="previewLoading" class="loading">{{ t('setup.steps.preview.loading') }}</div>
        <div v-else-if="previewError" class="error">{{ previewError }}</div>
        <div v-else-if="preview">
          <div class="summary">
            <span>{{ t('setup.steps.preview.total') }}: <b>{{ preview.summary.total }}</b></span>
            <span>{{ t('setup.steps.preview.ok') }}: <b>{{ preview.summary.succeeded }}</b></span>
            <span v-if="preview.summary.failed">
              {{ t('setup.steps.preview.failed') }}: <b>{{ preview.summary.failed }}</b>
            </span>
          </div>

          <div class="tree-cards">
            <div class="tree-card">
              <div class="tree-header">{{ t('setup.steps.preview.now') }}</div>
              <div class="tree-body">
                <div v-for="node in sourceTree" :key="node.key"
                  class="tree-node" :style="{ paddingLeft: node.depth * 14 + 8 + 'px' }">
                  <span :class="node.isFile ? 'file-name' : 'folder-name'">{{ node.name }}</span>
                </div>
              </div>
            </div>
            <div class="tree-card">
              <div class="tree-header">{{ t('setup.steps.preview.after') }}</div>
              <div class="tree-body">
                <div v-for="node in destTree" :key="node.key"
                  class="tree-node" :style="{ paddingLeft: node.depth * 14 + 8 + 'px' }">
                  <span :class="node.isFile ? 'file-name' : 'folder-name'">{{ node.name }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="preview.errors.length" class="errors-block">
            <p class="errors-title">{{ t('setup.steps.preview.errors_title') }}</p>
            <div v-for="(e, i) in preview.errors" :key="i" class="preview-error">
              {{ e.file }}: {{ e.reason }}
            </div>
          </div>
        </div>
      </section>

      <!-- Step 5: Inbox path -->
      <section v-else-if="step === 5">
        <h1>{{ t('setup.steps.inbox.label') }}</h1>
        <p class="hint">{{ t('setup.steps.inbox.hint') }}</p>

        <div class="field">
          <label>{{ t('setup.steps.inbox.inbox_path') }}</label>
          <input v-model="inbox" type="text" placeholder="C:\inbox" :class="{ invalid: fieldErrors.inbox }" />
          <p class="field-hint" :class="{ 'field-hint-error': fieldErrors.inbox }">{{ t('setup.steps.inbox.inbox_path_hint') }}</p>
        </div>
        <p class="skip-hint">{{ t('setup.steps.inbox.skip_hint') }}</p>
      </section>

      <!-- Step 6: Summary + launch -->
      <section v-else-if="step === 6">
        <h1>{{ t('setup.steps.launch.label') }}</h1>
        <p class="hint">{{ t('setup.steps.launch.hint') }}</p>

        <div class="summary-list">
          <div class="summary-row">
            <span>{{ t('setup.archive_path') }}</span><b>{{ archive }}</b>
          </div>
          <div class="summary-row">
            <span>{{ t('setup.username') }}</span><b>{{ username }}</b>
          </div>
          <div v-if="inbox" class="summary-row">
            <span>{{ t('setup.steps.inbox.inbox_path') }}</span><b>{{ inbox }}</b>
          </div>
          <div v-if="hasExisting && importPath" class="summary-row">
            <span>{{ t('setup.steps.launch.import_from') }}</span><b>{{ importPath }}</b>
          </div>
        </div>
      </section>

      <!-- Step 7: Processing -->
      <section v-else-if="step === 7">
        <h1>{{ t('setup.steps.processing.label') }}</h1>

        <div v-if="importing">
          <p class="hint">{{ t('setup.steps.processing.importing') }}</p>
          <div class="progress-row">
            <span>{{ t('setup.steps.preview.ok') }}: {{ importProgress.succeeded }}</span>
            <span v-if="importProgress.failed"> · {{ t('setup.steps.preview.failed') }}: {{ importProgress.failed }}</span>
          </div>
        </div>

        <div v-if="!importing" class="done-msg">{{ t('setup.steps.processing.done') }}</div>
      </section>

        <p v-if="error" class="error">{{ error }}</p>
        </div><!-- /setup-content -->

        <!-- Navigation -->
        <div class="nav">
          <button v-if="step > 1 && step <= 6 && !launched" type="button" class="btn-back" @click="back">
            {{ t('setup.back') }}
          </button>
          <button v-if="step < 6 && !launched" type="button" class="btn-next"
            :disabled="!canAdvance || previewLoading || validating" @click="next">
            {{ t('setup.next') }}
          </button>
          <button v-if="step === 6 && !launched" type="button" class="btn-next"
            :disabled="loading" @click="submit">
            {{ t('setup.submit') }}
          </button>
          <button v-if="step === 7 && !importing" type="button" class="btn-next" @click="finish">
            {{ t('setup.steps.processing.go') }}
          </button>
        </div>
      </div><!-- /setup-main -->
    </div><!-- /setup-box -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiUrl } from '../api.js'

const { t, locale } = useI18n()

function saveLang(lang) {
  localStorage.setItem('lang', lang)
}
const router = useRouter()

// Steps: 1=account+archive, 2=existing?, 3=import settings, 4=preview, 5=inbox, 6=summary
const step = ref(1)

// Step 1
const archive = ref('')
const username = ref('')
const password = ref('')
const password2 = ref('')

// Step 2
const hasExisting = ref(null)

// Step 3
const importPath = ref('')
const importRecursive = ref(false)

// Step 4
const preview = ref(null)
const previewLoading = ref(false)
const previewError = ref('')

// Step 5
const inbox = ref('')

// Final
const error = ref('')
const fieldErrors = ref({})
const validating = ref(false)
const loading = ref(false)
const launched = ref(false)
const importing = ref(false)
const importProgress = ref({ done: false, succeeded: 0, failed: 0, errors: [] })

function buildTree(paths) {
  if (!paths.length) return []

  // Build nested object from all path components
  const root = {}
  for (const p of paths) {
    const parts = p.replace(/\\/g, '/').split('/').filter(Boolean)
    let node = root
    for (const part of parts) {
      if (!node[part]) node[part] = {}
      node = node[part]
    }
  }

  // Flatten to renderable list
  const result = []
  function traverse(node, depth, parentKey) {
    for (const [name, children] of Object.entries(node).sort()) {
      const key = parentKey + '/' + name
      const isFile = Object.keys(children).length === 0
      result.push({ key, name, depth, isFile })
      if (!isFile) traverse(children, depth + 1, key)
    }
  }
  traverse(root, 0, '')
  return result
}

const sourceTree = computed(() =>
  preview.value ? buildTree(preview.value.sample.map(e => e.source)) : []
)
const destTree = computed(() =>
  preview.value ? buildTree(preview.value.sample.map(e => e.destination)) : []
)

const stepLabels = computed(() => [
  { n: 1, label: t('setup.steps.archive.label') },
  { n: 2, label: t('setup.steps.existing.label') },
  { n: 3, label: t('setup.steps.import.label'), skip: hasExisting.value === false },
  { n: 4, label: t('setup.steps.preview.label'), skip: hasExisting.value === false },
  { n: 5, label: t('setup.steps.inbox.label') },
  { n: 6, label: t('setup.steps.launch.label') },
  { n: 7, label: t('setup.steps.processing.label') },
])

function stepState(s) {
  if (s.skip) return 'skipped'
  if (s.n < step.value) return 'done'
  if (s.n === step.value) return 'active'
  return 'pending'
}

function stepIcon(s) {
  if (s.skip) return '–'
  if (s.n < step.value) return '✔'
  return ''
}

const canAdvance = computed(() => {
  if (step.value === 4) return !!preview.value
  return true
})

function back() {
  fieldErrors.value = {}
  if (step.value === 3 || step.value === 2) {
    step.value = step.value - 1
  } else if (step.value === 4) {
    step.value = 3
  } else if (step.value === 5 && !hasExisting.value) {
    step.value = 2
  } else {
    step.value = step.value - 1
  }
}

async function validateStep(stepNum) {
  validating.value = true
  fieldErrors.value = {}
  try {
    const res = await fetch(apiUrl('/setup/validate'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        step: stepNum,
        archive: archive.value,
        username: username.value,
        password: password.value,
        password2: password2.value,
        import_path: importPath.value,
        inbox: inbox.value,
      }),
    })
    const data = await res.json()
    fieldErrors.value = data.fields || {}
    return Object.keys(fieldErrors.value).length === 0
  } catch {
    return true
  } finally {
    validating.value = false
  }
}

async function next() {
  error.value = ''
  if (step.value === 1 || step.value === 3 || step.value === 5) {
    const ok = await validateStep(step.value)
    if (!ok) return
  }
  if (step.value === 2) {
    if (hasExisting.value === null) {
      fieldErrors.value = { choice: 'required' }
      return
    }
    if (!hasExisting.value) {
      step.value = 5
      return
    }
  }
  if (step.value === 3) {
    await loadPreview()
    step.value = 4
    return
  }
  step.value = step.value + 1
}

async function loadPreview() {
  previewLoading.value = true
  previewError.value = ''
  preview.value = null
  try {
    const res = await fetch(apiUrl('/setup/preview'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input_path: importPath.value,
        output_path: archive.value,
        recursive: importRecursive.value,
      }),
    })
    if (!res.ok) {
      const d = await res.json()
      previewError.value = d.detail || t('setup.error_unavailable')
    } else {
      preview.value = await res.json()
    }
  } catch {
    previewError.value = t('setup.error_unavailable')
  } finally {
    previewLoading.value = false
  }
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await fetch(apiUrl('/setup'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        archive: archive.value,
        username: username.value,
        password: password.value,
        inbox: inbox.value,
        import_path: hasExisting.value ? importPath.value : '',
        import_recursive: importRecursive.value,
      }),
    })
    if (!res.ok) {
      const d = await res.json()
      error.value = d.detail || t('setup.error_unavailable')
      return
    }
    const data = await res.json()
    launched.value = true
    step.value = 7
    if (data.importing) {
      importing.value = true
      listenProgress()
    }
  } catch {
    error.value = t('setup.error_unavailable')
  } finally {
    loading.value = false
  }
}

function listenProgress() {
  const es = new EventSource(apiUrl('/setup/import/progress'))
  es.onmessage = (e) => {
    const p = JSON.parse(e.data)
    importProgress.value = p
    if (p.done) {
      importing.value = false
      es.close()
    }
  }
  es.onerror = () => es.close()
}

onMounted(async () => {
  try {
    const res = await fetch(apiUrl('/setup/status'))
    const data = await res.json()
    if (data.import_status === 'running') {
      launched.value = true
      importing.value = true
      step.value = 7
      listenProgress()
    } else if (data.import_status === 'done') {
      launched.value = true
      importing.value = false
      step.value = 7
      if (data.import_result) {
        importProgress.value = {
          done: true,
          total: data.import_result.total,
          succeeded: data.import_result.succeeded,
          failed: data.import_result.failed,
          errors: [],
        }
      }
    } else if (data.import_status === 'interrupted') {
      launched.value = true
      importing.value = false
      step.value = 7
      error.value = t('setup.error_import_interrupted')
    }
  } catch {
    // ignore — show normal step 1
  }
})

async function finish() {
  try {
    await fetch(apiUrl('/setup/finish'), { method: 'POST' })
  } catch { /* ignore */ }
  router.push('/login')
}
</script>

<style scoped>
.setup-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  overflow: hidden;
}
.setup-box {
  width: 860px;
  height: calc(100vh - 4rem);
  display: flex;
  flex-direction: row;
}
.setup-sidebar {
  width: 185px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: 2.8rem;
  padding-right: 2rem;
  border-right: 1px solid var(--border);
  gap: 0.1rem;
}
.step-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0;
  font-size: 0.88rem;
  color: var(--text);
  line-height: 1.3;
}
.step-item.active {
  color: var(--text);
  font-weight: 600;
}
.step-item.done { color: var(--accent); font-weight: 600; }
.step-item.skipped { opacity: 0.3; }
.step-icon {
  width: 1rem;
  flex-shrink: 0;
  font-size: 0.85rem;
  color: inherit;
}
.step-label { min-width: 0; }
.setup-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-left: 2rem;
  min-width: 0;
}
.setup-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-bottom: 1rem;
}
.lang-bar {
  display: flex;
  justify-content: flex-end;
  gap: 0.4rem;
  margin-bottom: 1rem;
}
.lang-btn {
  padding: 0.2rem 0.5rem;
  font-size: 0.75rem;
  border: 1px solid var(--border);
  border-radius: 3px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}
.lang-btn.active {
  color: var(--accent);
  border-color: var(--accent);
}
h1 {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.4rem;
}
.hint {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin-bottom: 1.25rem;
}
.skip-hint {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}
.field {
  margin-bottom: 0.85rem;
}
.field.checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.field.checkbox label {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text);
}
label {
  display: block;
  font-size: 0.8rem;
  color: var(--text);
  margin-bottom: 0.3rem;
}
input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 0.5rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: #fff;
  color: var(--text);
  font-size: 0.9rem;
  box-sizing: border-box;
}
input:focus {
  outline: none;
  border-color: var(--accent);
}
input.invalid {
  border-color: var(--danger);
}
input.invalid:focus {
  border-color: var(--danger);
}
.field-hint {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}
.field-hint-error {
  color: var(--danger);
}
.choice {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}
.choice-btn {
  flex: 1;
  padding: 0.7rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: #fff;
  color: var(--text);
  font-size: 0.9rem;
  cursor: pointer;
}
.choice-btn.selected {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, #fff);
}
.summary {
  display: flex;
  gap: 1.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}
.tree-cards {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}
.tree-card {
  min-width: 0;
}
.tree-header {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.4rem;
}
.tree-body {
  padding: 0;
}
.tree-node {
  white-space: nowrap;
}
.tree-node {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0;
  font-size: 0.8rem;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
}
.folder-name { overflow: hidden; text-overflow: ellipsis; font-weight: 500; color: var(--text); }
.file-name { overflow: hidden; text-overflow: ellipsis; color: var(--text-muted); font-size: 0.78rem; }
.errors-block {
  margin-top: 1.75rem;
  font-size: 0.78rem;
  color: var(--text-muted);
}
.errors-title { font-size: 0.9rem; font-weight: 600; margin-bottom: 0.4rem; color: var(--text); }
.summary-list { margin-bottom: 1.5rem; }
.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted);
}
.summary-row b { color: var(--text); }
.progress-row {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}
.done-msg {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--text);
  font-weight: 500;
}
.nav {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1.25rem;
}
.btn-back {
  width: 120px;
  padding: 0.5rem 0;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: #fff;
  color: var(--text-muted);
  font-size: 0.9rem;
  cursor: pointer;
}
.btn-next {
  width: 120px;
  margin-left: auto;
  padding: 0.55rem 0;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  text-align: center;
}
.btn-next:disabled {
  opacity: 0.5;
  cursor: default;
}
.error {
  font-size: 0.82rem;
  color: var(--danger);
  margin: 0.5rem 0;
}
.loading {
  font-size: 0.85rem;
  color: var(--text-muted);
  padding: 1rem 0;
}
</style>
