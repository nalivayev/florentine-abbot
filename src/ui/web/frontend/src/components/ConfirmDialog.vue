<template>
  <Teleport to="body">
    <div class="overlay" v-if="visible" @click.self="cancel">
      <div class="dialog">
        <div class="dialog-title">{{ title || t('confirm.title') }}</div>
        <div class="dialog-message">{{ message }}</div>
        <div class="dialog-actions">
          <button class="btn btn-cancel" @click="cancel">{{ t('confirm.cancel') }}</button>
          <button class="btn btn-confirm" @click="confirm">{{ confirmLabel || t('confirm.confirm') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  visible: Boolean,
  title: String,
  message: String,
  confirmLabel: String,
})

const emit = defineEmits(['confirm', 'cancel'])
const confirm = () => emit('confirm')
const cancel = () => emit('cancel')

function onKeydown(e) {
  if (e.key === 'Escape') cancel()
}

watch(() => props.visible, (v) => {
  if (v) document.addEventListener('keydown', onKeydown)
  else document.removeEventListener('keydown', onKeydown)
})
</script>
