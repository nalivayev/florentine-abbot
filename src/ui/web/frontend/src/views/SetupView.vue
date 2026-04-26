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

          <div class="wizard-column setup-wizard">
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
            <input v-model="archivePath" type="text" placeholder="C:\archive" :class="{ invalid: fieldErrors.archive_path }" />
            <p class="field-hint" :class="{ 'field-hint-error': fieldErrors.archive_path }">{{ t('setup.steps.archive.archive_path_hint') }}</p>
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

      <!-- Step 4: Launch -->
      <section v-else-if="step === 4">
        <h1>{{ t('setup.steps.launch.label') }}</h1>
        <p class="hint">{{ t('setup.steps.launch.hint') }}</p>

        <div class="summary-list">
          <div class="summary-row">
            <span>{{ t('setup.archive_path') }}</span><b>{{ archivePath }}</b>
          </div>
          <div class="summary-row">
            <span>{{ t('setup.username') }}</span><b>{{ username }}</b>
          </div>
        </div>
      </section>

        <p v-if="error" class="error">{{ error }}</p>
        </div><!-- /setup-content -->

        <!-- Navigation -->
        <div class="wizard-nav">
          <button v-if="step > 1" type="button" class="btn-back" @click="back">
            {{ t('setup.back') }}
          </button>
          <button v-if="step < 4" type="button" class="btn-next"
            :disabled="!canAdvance || validating || exiftoolChecking" @click="next">
            {{ t('setup.next') }}
          </button>
          <button v-if="step === 4" type="button" class="btn-next"
            :disabled="loading" @click="submit">
            {{ t('setup.submit') }}
          </button>
        </div>
        </div>
      </div><!-- /setup-main -->
    </div><!-- /setup-box -->
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from '../theme.js'
import { apiUrl } from '../api.js'

const { t, locale } = useI18n()
const { isDark, init: initTheme, toggle } = useTheme()

function saveLang(lang) {
  localStorage.setItem('lang', lang)
}

// Steps: 1=welcome, 2=sysreq, 3=account+archive, 4=launch
const step = ref(1)

const archivePath = ref('')
const username = ref('')
const password = ref('')
const password2 = ref('')

const exiftoolChecked = ref(false)
const exiftoolChecking = ref(false)
const exiftoolInstalled = ref(false)
const exiftoolVersion = ref(null)

const error = ref('')
const fieldErrors = ref({})
const validating = ref(false)
const loading = ref(false)

const stepLabels = computed(() => [
  { n: 1, label: t('setup.steps.welcome.label') },
  { n: 2, label: t('setup.steps.sysreq.label') },
  { n: 3, label: t('setup.steps.archive.label') },
  { n: 4, label: t('setup.steps.launch.label') },
])

function stepState(s) {
  if (s.n < step.value) return 'done'
  if (s.n === step.value) return 'active'
  return 'pending'
}

function stepIcon(s) {
  return s.n < step.value ? '✔' : ''
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
        archive_path: archivePath.value,
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
        archive_path: archivePath.value,
        username: username.value,
        password: password.value,
      }),
    })
    if (!res.ok) {
      const d = await res.json()
      error.value = d.detail || t('setup.error_unavailable')
      return
    }
    window.location.href = '/'
  } catch {
    error.value = t('setup.error_unavailable')
  } finally {
    loading.value = false
  }
}

initTheme()
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
.setup-wizard {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
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
  padding: var(--inset-chip-y) var(--sp-2);
  font-size: var(--fs-xs);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
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
.setup-section { margin-bottom: var(--sp-6); }
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
  padding: var(--inset-control-y) var(--inset-control-x);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
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
.error { font-size: var(--fs-sm); color: var(--danger); margin: var(--sp-2) 0; }
.loading { font-size: var(--fs-base); color: var(--text-muted); padding: var(--sp-4) 0; }
.exiftool-warning {
  margin-top: var(--sp-5);
  padding: 0.9rem var(--sp-4);
  background: var(--bg-warning);
  border-left: 3px solid var(--warning);
  border-radius: 0 var(--radius-xs) var(--radius-xs) 0;
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
  border-radius: var(--radius-xs);
  padding: var(--sp-2) var(--sp-3);
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
