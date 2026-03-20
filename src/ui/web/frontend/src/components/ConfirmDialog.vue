<template>
  <Teleport to="body">
    <div class="overlay" v-if="visible" @click.self="cancel">
      <div class="dialog">
        <div class="dialog-title">{{ title }}</div>
        <div class="dialog-message">{{ message }}</div>
        <div class="dialog-actions">
          <button class="btn btn-cancel" @click="cancel">{{ t('confirm.cancel') }}</button>
          <button class="btn btn-confirm" @click="confirm">{{ confirmLabel }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

defineProps({
  visible: Boolean,
  title: { type: String, default: 'Подтверждение' },
  message: String,
  confirmLabel: { type: String, default: 'Продолжить' },
})

const emit = defineEmits(['confirm', 'cancel'])
const confirm = () => emit('confirm')
const cancel = () => emit('cancel')
</script>
