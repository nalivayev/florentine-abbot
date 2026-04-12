<template>
  <Teleport to="body">
    <div class="overlay" @click.self="cancel">
      <div class="dialog" ref="dialogEl" @keydown="trapFocus">
        <div class="dialog-title">{{ title }}</div>
        <p class="dialog-hint">{{ hint }}</p>

        <div class="field">
          <input
            ref="inputEl"
            class="template-input"
            v-model="draft"
            spellcheck="false"
            @input="validateDraft"
          />
          <p v-if="draftError" class="input-error">{{ draftError }}</p>
        </div>

        <div class="preview-block">
          <span class="preview-label">{{ t('setup.steps.format.preview_label') }}:</span>
          <code class="preview-value"><span v-if="prefix" class="preview-prefix">{{ prefix }}</span>{{ previewResult }}</code>
        </div>

        <div class="tags-section">
          <div class="tags-label">{{ t('setup.steps.format.tags_label') }}</div>
          <div class="tags-list">
            <div
              v-for="tag in tags"
              :key="tag.name"
              class="tag-item"
              :title="tag.description"
              @click="insertTag(tag.name)"
            >
              <code class="tag-chip">{{ '{' + tag.name + '}' }}</code>
              <span class="tag-desc">{{ tag.description }}</span>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <button class="btn btn-cancel" @click="cancel">{{ t('confirm.cancel') }}</button>
          <button class="btn btn-confirm" :disabled="!!draftError" @click="apply">{{ t('confirm.confirm') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: { type: String, required: true },
  title: { type: String, required: true },
  hint: { type: String, required: true },
  prefix: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'close'])

const { t } = useI18n()

const draft = ref(props.modelValue)
const draftError = ref('')
const inputEl = ref(null)
const dialogEl = ref(null)

onMounted(() => {
  nextTick(() => inputEl.value?.focus())
  window.addEventListener('keydown', onEsc)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onEsc)
})

function onEsc(e) {
  if (e.key === 'Escape') cancel()
}

function trapFocus(e) {
  if (e.key !== 'Tab') return
  const focusable = Array.from(dialogEl.value.querySelectorAll(
    'button:not(:disabled), input:not(:disabled)'
  ))
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (e.shiftKey) {
    if (document.activeElement === first) { e.preventDefault(); last.focus() }
  } else {
    if (document.activeElement === last) { e.preventDefault(); first.focus() }
  }
}

watch(() => props.modelValue, v => { draft.value = v })

const SAMPLE = {
  year: 2024, month: 5, day: 12,
  hour: 14, minute: 30, second: 0,
  sequence: 1,
  modifier: 'E', group: 'FAM', subgroup: 'POR',
  side: 'A', suffix: 'MSR',
}

const KNOWN_TAGS = ['year','month','day','hour','minute','second','sequence','modifier','group','subgroup','side','suffix']

const tags = computed(() =>
  KNOWN_TAGS.map(name => ({
    name,
    description: t(`setup.steps.format.tags.${name}`),
  }))
)

function renderTemplate(tpl) {
  return tpl.replace(/\{(\w+)(?::([^}]+))?\}/g, (_, name, fmt) => {
    const val = SAMPLE[name]
    if (val === undefined) return `{${name}}`
    if (fmt && typeof val === 'number') {
      const width = parseInt(fmt)
      if (!isNaN(width)) return String(val).padStart(width, '0')
    }
    return String(val)
  })
}

const previewResult = computed(() => renderTemplate(draft.value))

function validateDraft() {
  const unknown = [...draft.value.matchAll(/\{(\w+)(?::[^}]*)?\}/g)]
    .map(m => m[1])
    .filter(name => !KNOWN_TAGS.includes(name))
  draftError.value = unknown.length
    ? t('setup.steps.format.unknown_tags', { tags: unknown.map(n => `{${n}}`).join(', ') })
    : ''
}

function insertTag(name) {
  const el = inputEl.value
  if (!el) { draft.value += `{${name}}`; return }
  const start = el.selectionStart ?? draft.value.length
  const end = el.selectionEnd ?? draft.value.length
  draft.value = draft.value.slice(0, start) + `{${name}}` + draft.value.slice(end)
  validateDraft()
  nextTick(() => {
    const pos = start + name.length + 2
    el.focus()
    el.setSelectionRange(pos, pos)
  })
}

function apply() {
  if (draftError.value) return
  emit('update:modelValue', draft.value)
  emit('close')
}

function cancel() {
  emit('close')
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.dialog {
  background: var(--surface);
  border-radius: 6px;
  padding: var(--sp-6);
  width: 560px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  overflow: hidden;
}
.dialog-title {
  font-size: var(--fs-lg);
  font-weight: 600;
  color: var(--text);
}
.dialog-hint {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  margin: 0;
}
.template-input {
  width: 100%;
  padding: var(--sp-2) 0.6rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-family: monospace;
  font-size: var(--fs-base);
  color: var(--text);
  box-sizing: border-box;
}
.template-input:focus {
  outline: none;
  border-color: var(--accent);
}
.input-error {
  font-size: var(--fs-xs);
  color: var(--danger);
  margin: 0.2rem 0 0;
}
.preview-block {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  font-size: var(--fs-sm);
}
.preview-label { color: var(--text-muted); white-space: nowrap; }
.preview-prefix { color: var(--text-muted); }
.preview-value {
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--text);
  word-break: break-all;
}
.tags-section {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  border-top: 1px solid var(--border);
  padding-top: var(--sp-3);
}
.tags-label {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text);
  margin: 0 0 var(--sp-2);
}
.tags-list {
  display: flex;
  flex-direction: column;
}
.tag-item {
  display: grid;
  grid-template-columns: 8rem 1fr;
  align-items: baseline;
  gap: var(--sp-2);
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
}
.tag-item:hover { background: var(--bg); }
.tag-chip {
  font-family: monospace;
  font-size: var(--fs-sm);
  color: var(--accent);
  white-space: nowrap;
}
.tag-desc {
  font-size: var(--fs-sm);
  color: var(--text-muted);
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
}
</style>
