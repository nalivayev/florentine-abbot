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
        <!-- Language + theme switcher -->
        <div class="lang-bar">
          <button class="lang-btn theme-btn" @click="toggle" :title="isDark ? 'Light' : 'Dark'">{{ isDark ? '☀' : '☽' }}</button>
          <span class="switcher-sep">|</span>
          <button v-for="lang in ['ru', 'en']" :key="lang"
            :class="['lang-btn', { active: locale === lang }]"
            @click="locale = lang; saveLang(lang)">{{ lang.toUpperCase() }}</button>
        </div>

        <div class="setup-content">

      <!-- Step 1: Welcome -->
      <section v-if="step === 1">
        <h1>{{ t('setup.steps.welcome.label') }}</h1>
        <p class="hint hint-preline">{{ t('setup.steps.welcome.hint') }}</p>
      </section>

      <!-- Step 2: System requirements -->
      <section v-else-if="step === 2">
        <h1>{{ t('setup.steps.sysreq.label') }}</h1>

        <div v-if="exiftoolChecking" class="loading">{{ t('setup.steps.sysreq.checking') }}</div>

        <div v-else-if="exiftoolChecked && exiftoolInstalled" class="sysreq-row">
          <span>ExifTool</span><span class="sysreq-ok">✔ {{ exiftoolVersion }}</span>
        </div>

        <div v-else-if="exiftoolChecked && !exiftoolInstalled" class="exiftool-warning">
          <p class="exiftool-title">⚠ {{ t('setup.exiftool.missing_title') }}</p>
          <p class="exiftool-text">{{ t('setup.exiftool.missing_hint') }}</p>
          <pre class="exiftool-cmd">{{ exiftoolCmd }}</pre>
          <button type="button" class="btn-back" @click="checkExiftool">
            {{ t('setup.exiftool.recheck') }}
          </button>
        </div>
      </section>

      <!-- Step 3: Account + Archive -->
      <section v-else-if="step === 3">
        <h1>{{ t('setup.steps.archive.label') }}</h1>

        <div class="setup-section">
          <p class="subsection-label">{{ t('setup.steps.archive.archive_section_label') }}</p>
          <div class="field">
            <label>{{ t('setup.archive_path') }}</label>
            <input v-model="archive" type="text" placeholder="C:\archive" :class="{ invalid: fieldErrors.archive }" />
            <p class="field-hint" :class="{ 'field-hint-error': fieldErrors.archive }">{{ t('setup.steps.archive.archive_path_hint') }}</p>
          </div>
        </div>

        <div class="setup-section">
          <p class="subsection-label">{{ t('setup.steps.archive.admin_account_label') }}</p>
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
        </div>
      </section>

      <!-- Step 4: Archive format -->
      <section v-else-if="step === 4">
        <h1>{{ t('setup.steps.format.label') }}</h1>
        <p class="hint">{{ t('setup.steps.format.hint') }}</p>

        <p class="tree-caption">{{ t('setup.steps.format.tree_caption') }}</p>
        <div class="archive-tree">
          <div class="tree-node tree-dir tree-d0">{{ archive || t('setup.steps.format.tree_archive') }}/</div>
          <div class="tree-node tree-dir tree-d1">{{ treeYearFolder }}/</div>

          <!-- date with two photos -->
          <div class="tree-node tree-dir tree-d2">{{ treeDateFolder1 }}/</div>
          <div class="tree-node tree-dir tree-d3">SOURCES/</div>
          <div class="tree-node tree-locked tree-d4">{{ treeFileMSR1a }}.tiff</div>
          <div class="tree-node tree-locked tree-d4">{{ treeFileRAW1a }}.cr2</div>
          <div class="tree-node tree-locked tree-d4">{{ treeFileMSR1b }}.tiff</div>
          <div class="tree-node tree-locked tree-d4">{{ treeFileRAW1b }}.cr2</div>
          <div class="tree-node tree-dir tree-d3">DERIVATIVES/</div>
          <div class="tree-node tree-muted tree-d4">{{ treeFilePRT1a }}.tiff</div>
          <div class="tree-node tree-muted tree-d4">{{ treeFileWEB1a }}.jpg</div>
          <div class="tree-node tree-muted tree-d4">{{ treeFilePRT1b }}.tiff</div>
          <div class="tree-node tree-muted tree-d4">{{ treeFileWEB1b }}.jpg</div>
          <div class="tree-node tree-d3">{{ treeFilePRV1a }}.jpg</div>
          <div class="tree-node tree-d3">{{ treeFilePRV1b }}.jpg</div>

          <!-- date with one photo -->
          <div class="tree-node tree-dir tree-d2">{{ treeDateFolder2 }}/</div>
          <div class="tree-node tree-dir tree-d3">SOURCES/</div>
          <div class="tree-node tree-locked tree-d4">{{ treeFileMSR2 }}.tiff</div>
          <div class="tree-node tree-locked tree-d4">{{ treeFileRAW2 }}.cr2</div>
          <div class="tree-node tree-dir tree-d3">DERIVATIVES/</div>
          <div class="tree-node tree-muted tree-d4">{{ treeFilePRT2 }}.tiff</div>
          <div class="tree-node tree-muted tree-d4">{{ treeFileWEB2 }}.jpg</div>
          <div class="tree-node tree-d3">{{ treeFilePRV2 }}.jpg</div>
        </div>

        <dl class="tree-legend">
          <dt>SOURCES/</dt><dd>{{ t('setup.steps.format.legend_sources') }}</dd>
          <dt>DERIVATIVES/</dt><dd>{{ t('setup.steps.format.legend_derivatives') }}</dd>
          <dt>*.PRV.*</dt><dd>{{ t('setup.steps.format.legend_prv') }}</dd>
        </dl>

        <div class="format-edit-links">
          <button type="button" class="btn-edit" @click="openDialog('path')">{{ t('setup.steps.format.edit_path') }}</button>
          <button type="button" class="btn-edit" @click="openDialog('filename')">{{ t('setup.steps.format.edit_filename') }}</button>
        </div>
      </section>

      <!-- Step 5: Launch -->
      <section v-else-if="step === 5">
        <h1>{{ t('setup.steps.launch.label') }}</h1>
        <p class="hint">{{ t('setup.steps.launch.hint') }}</p>

        <div class="summary-list">
          <div class="summary-row">
            <span>{{ t('setup.archive_path') }}</span><b>{{ archive }}</b>
          </div>
          <div class="summary-row">
            <span>{{ t('setup.username') }}</span><b>{{ username }}</b>
          </div>
          <div class="summary-row">
            <span>{{ t('setup.steps.format.path_label') }}</span>
            <code class="summary-code">{{ archivePathTemplate }}</code>
          </div>
          <div class="summary-row">
            <span>{{ t('setup.steps.format.filename_label') }}</span>
            <code class="summary-code">{{ archiveFilenameTemplate }}</code>
          </div>
        </div>
      </section>

        <p v-if="error" class="error">{{ error }}</p>
        </div><!-- /setup-content -->

        <!-- Navigation -->
        <div class="nav">
          <button v-if="step > 1" type="button" class="btn-back" @click="back">
            {{ t('setup.back') }}
          </button>
          <button v-if="step < 5" type="button" class="btn-next"
            :disabled="!canAdvance || validating || exiftoolChecking" @click="next">
            {{ t('setup.next') }}
          </button>
          <button v-if="step === 5" type="button" class="btn-next"
            :disabled="loading" @click="submit">
            {{ t('setup.submit') }}
          </button>
        </div>
      </div><!-- /setup-main -->
    </div><!-- /setup-box -->
  </div>

  <!-- Format edit dialogs -->
  <FormatEditDialog
    v-if="dialogOpen === 'path'"
    v-model="archivePathTemplate"
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
import { useTheme } from '../theme.js'
import { apiUrl } from '../api.js'
import FormatEditDialog from '../components/FormatEditDialog.vue'

const { t, locale } = useI18n()
const { isDark, init: initTheme, toggle } = useTheme()

function saveLang(lang) {
  localStorage.setItem('lang', lang)
}

// Steps: 1=welcome, 2=sysreq, 3=account+archive, 4=format, 5=launch
const step = ref(1)

// Step 3
const archive = ref('')
const username = ref('')
const password = ref('')
const password2 = ref('')

// Step 4
const archivePathTemplate = ref('')
const archiveFilenameTemplate = ref('')
const dialogOpen = ref(null)

// ExifTool
const exiftoolChecked = ref(false)
const exiftoolChecking = ref(false)
const exiftoolInstalled = ref(false)
const exiftoolVersion = ref(null)

// Final
const error = ref('')
const fieldErrors = ref({})
const validating = ref(false)
const loading = ref(false)

const SAMPLE = {
  year: 2024, month: 5, day: 12,
  hour: 14, minute: 30, second: 0,
  sequence: 1,
  modifier: 'E', group: 'FAM', subgroup: 'POR',
  side: 'A', suffix: 'MSR',
}

function renderTplWith(tpl, overrides = {}) {
  const sample = { ...SAMPLE, ...overrides }
  return tpl.replace(/\{(\w+)(?::([^}]+))?\}/g, (_, name, fmt) => {
    const val = sample[name]
    if (val === undefined) return `{${name}}`
    if (fmt && typeof val === 'number') {
      const width = parseInt(fmt)
      if (!isNaN(width)) return String(val).padStart(width, '0')
    }
    return String(val)
  })
}


// S1a, S1b — two photos on the same date (day 11); S2 — one photo on a different date (day 12)
const S1a = { day: 11, hour: 10, minute: 15, second: 0, sequence: 1 }
const S1b = { day: 11, hour: 14, minute: 30, second: 0, sequence: 2 }
const S2  = {}

const treeYearFolder  = computed(() => renderTplWith(archivePathTemplate.value, S2).split('/')[0])
const treeDateFolder1 = computed(() => { const p = renderTplWith(archivePathTemplate.value, S1a).split('/'); return p[p.length - 1] })
const treeDateFolder2 = computed(() => { const p = renderTplWith(archivePathTemplate.value, S2).split('/'); return p[p.length - 1] })

const treeFileMSR1a = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1a, suffix: 'MSR' }))
const treeFileRAW1a = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1a, suffix: 'RAW' }))
const treeFilePRV1a = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1a, suffix: 'PRV' }))
const treeFilePRT1a = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1a, suffix: 'PRT' }))
const treeFileWEB1a = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1a, suffix: 'WEB' }))
const treeFileMSR1b = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1b, suffix: 'MSR' }))
const treeFileRAW1b = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1b, suffix: 'RAW' }))
const treeFilePRV1b = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1b, suffix: 'PRV' }))
const treeFilePRT1b = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1b, suffix: 'PRT' }))
const treeFileWEB1b = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S1b, suffix: 'WEB' }))
const treeFileMSR2  = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S2,  suffix: 'MSR' }))
const treeFileRAW2  = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S2,  suffix: 'RAW' }))
const treeFilePRV2  = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S2,  suffix: 'PRV' }))
const treeFilePRT2  = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S2,  suffix: 'PRT' }))
const treeFileWEB2  = computed(() => renderTplWith(archiveFilenameTemplate.value, { ...S2,  suffix: 'WEB' }))

const stepLabels = computed(() => [
  { n: 1, label: t('setup.steps.welcome.label') },
  { n: 2, label: t('setup.steps.sysreq.label') },
  { n: 3, label: t('setup.steps.archive.label') },
  { n: 4, label: t('setup.steps.format.label') },
  { n: 5, label: t('setup.steps.launch.label') },
])

function stepState(s) {
  if (s.n < step.value) return 'done'
  if (s.n === step.value) return 'active'
  return 'pending'
}

function stepIcon(s) {
  return s.n < step.value ? '✔' : ''
}

function openDialog(which) {
  dialogOpen.value = which
}

const canAdvance = computed(() => {
  if (step.value === 2) return exiftoolChecked.value && exiftoolInstalled.value
  return true
})

function back() {
  fieldErrors.value = {}
  step.value = step.value - 1
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

const exiftoolCmd = computed(() => {
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('win')) return 'winget install --id OliverBetz.ExifTool -e'
  if (ua.includes('mac')) return 'brew install exiftool'
  return 'sudo apt install libimage-exiftool-perl'
})

async function checkExiftool() {
  exiftoolChecking.value = true
  try {
    const res = await fetch(apiUrl('/setup/check-exiftool'))
    const data = await res.json()
    exiftoolInstalled.value = data.installed
    exiftoolVersion.value = data.version
  } catch {
    exiftoolInstalled.value = false
    exiftoolVersion.value = null
  }
  exiftoolChecked.value = true
  exiftoolChecking.value = false
  return exiftoolInstalled.value
}

async function next() {
  error.value = ''
  if (step.value === 1) {
    step.value = 2
    const ok = await checkExiftool()
    if (ok) step.value = 3
    return
  }
  if (step.value === 2) {
    if (!exiftoolChecked.value) await checkExiftool()
    if (!exiftoolInstalled.value) return
  }
  if (step.value === 3) {
    const ok = await validateStep(3)
    if (!ok) return
  }
  step.value = step.value + 1
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
        archive_path_template: archivePathTemplate.value,
        archive_filename_template: archiveFilenameTemplate.value,
      }),
    })
    if (!res.ok) {
      const d = await res.json()
      error.value = d.detail || t('setup.error_unavailable')
      return
    }
    window.location.href = '/admin/login'
  } catch {
    error.value = t('setup.error_unavailable')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  initTheme()
  try {
    const res = await fetch(apiUrl('/setup/format'))
    const data = await res.json()
    archivePathTemplate.value = data.archive_path_template
    archiveFilenameTemplate.value = data.archive_filename_template
  } catch {
    archivePathTemplate.value = '{year:04d}/{year:04d}.{month:02d}.{day:02d}'
    archiveFilenameTemplate.value = '{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}'
  }
})
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
  width: min(1040px, calc(100vw - 4rem));
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
  padding-right: var(--sp-7);
  border-right: 1px solid var(--border);
  gap: 0.1rem;
}
.step-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 0.4rem 0;
  font-size: var(--fs-base);
  color: var(--text);
  line-height: 1.3;
}
.step-item.active { color: var(--accent); font-weight: 600; }
.step-item.done { color: var(--text); font-weight: 600; }
.step-icon {
  width: var(--sp-4);
  flex-shrink: 0;
  font-size: var(--fs-base);
  color: inherit;
}
.step-label { min-width: 0; }
.setup-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-left: var(--sp-7);
  min-width: 0;
}
.setup-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-bottom: var(--sp-4);
}
.lang-bar {
  display: flex;
  justify-content: flex-end;
  gap: 0.4rem;
  margin-bottom: var(--sp-4);
}
.lang-btn {
  padding: 0.2rem var(--sp-2);
  font-size: var(--fs-xs);
  border: 1px solid var(--border);
  border-radius: 3px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}
.lang-btn.active { color: var(--accent); border-color: var(--accent); }
.switcher-sep {
  color: var(--border);
  font-size: var(--fs-sm);
  user-select: none;
}
h1 {
  font-size: var(--fs-lg);
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.4rem;
}
.hint {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  margin-bottom: var(--sp-5);
}
.hint-preline { white-space: pre-line; }
.exiftool-warning .btn-back { margin-top: var(--sp-3); }
.subsection-label {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text);
  margin: 0 0 var(--sp-2);
}
.field { margin-bottom: 0.85rem; }
label {
  display: block;
  font-size: var(--fs-sm);
  color: var(--text);
  margin-bottom: 0.3rem;
}
input[type="text"],
input[type="password"] {
  width: 100%;
  padding: var(--sp-2) 0.6rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-base);
  box-sizing: border-box;
}
input:focus { outline: none; border-color: var(--accent); }
input.invalid { border-color: var(--danger); }
input.invalid:focus { border-color: var(--danger); }
.field-hint {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-top: var(--sp-1);
}
.field-hint-error { color: var(--danger); }
/* Archive tree */
.tree-caption {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  margin: 0 0 0.4rem;
}
.archive-tree {
  font-family: monospace;
  font-size: var(--fs-sm);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.65rem 0.75rem;
  overflow-x: auto;
  margin-bottom: var(--sp-3);
}
.tree-node {
  white-space: nowrap;
  line-height: 1.7;
  color: var(--text);
}
.tree-d0 { padding-left: 0; }
.tree-d1 { padding-left: var(--sp-6); }
.tree-d2 { padding-left: 3rem; }
.tree-d3 { padding-left: 4.5rem; }
.tree-d4 { padding-left: 6rem; }
.tree-dir { font-weight: 500; }
.tree-locked { color: var(--text-muted); }
.tree-muted { color: var(--text-muted); }
.tree-legend {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.2rem var(--sp-3);
  font-size: var(--fs-xs);
  margin: var(--sp-4) 0 var(--sp-5);
}
.tree-legend dt {
  font-family: monospace;
  color: var(--text);
  white-space: nowrap;
}
.tree-legend dd {
  color: var(--text-muted);
  margin: 0;
}
.format-edit-links {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
}
/* Format step */
.setup-section {
  padding: var(--sp-3) 0;
  border-top: 1px solid var(--border);
}
.setup-section:last-of-type { border-bottom: 1px solid var(--border); }
.setup-section-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--sp-2);
}
.setup-section-title {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text);
  margin: 0 0 0.15rem;
}
.setup-section-desc {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin: 0;
}
.format-value {
  display: block;
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.35rem 0.6rem;
  word-break: break-all;
  margin-bottom: 0.45rem;
}
.format-preview-row {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  font-size: var(--fs-sm);
}
.preview-label { color: var(--text-muted); white-space: nowrap; flex-shrink: 0; }
.preview-value {
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text);
  word-break: break-all;
}
.btn-edit {
  flex-shrink: 0;
  padding: var(--sp-1) var(--sp-3);
  font-size: var(--fs-sm);
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text-muted);
  cursor: pointer;
}
.btn-edit:hover { border-color: var(--accent); color: var(--accent); }
/* Summary */
.summary-list { margin-bottom: var(--sp-6); }
.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--sp-4);
  font-size: var(--fs-base);
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted);
}
.summary-row b { color: var(--text); }
.summary-code {
  font-family: monospace;
  font-size: var(--fs-xs);
  color: var(--text);
  text-align: right;
  word-break: break-all;
}
/* Nav */
.nav {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--sp-5);
}
.btn-back {
  width: 120px;
  padding: var(--sp-2) 0;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text-muted);
  font-size: var(--fs-base);
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
  font-size: var(--fs-base);
  cursor: pointer;
  text-align: center;
}
.btn-next:disabled { opacity: 0.5; cursor: default; }
.error { font-size: var(--fs-sm); color: var(--danger); margin: var(--sp-2) 0; }
.loading { font-size: var(--fs-base); color: var(--text-muted); padding: var(--sp-4) 0; }
.exiftool-warning {
  margin-top: var(--sp-5);
  padding: 0.9rem var(--sp-4);
  background: var(--bg-warning);
  border-left: 3px solid var(--warning);
  border-radius: 0 4px 4px 0;
}
.sysreq-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-2) 0;
  font-size: var(--fs-base);
  color: var(--text);
}
.sysreq-ok { color: var(--success); font-weight: 500; }
.exiftool-title { font-weight: 600; font-size: var(--fs-base); color: var(--text); margin-bottom: 0.4rem; }
.exiftool-text { font-size: var(--fs-sm); color: var(--text-muted); margin-bottom: var(--sp-2); }
.exiftool-cmd {
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: var(--sp-2) var(--sp-3);
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
