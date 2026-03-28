<template>
  <div class="albums-page">
    <div class="albums-header">
      <h1 class="page-title">{{ t('app.albums.title') }}</h1>
    </div>

    <div class="albums-empty">
      <p class="empty-icon">🗂</p>
      <p class="empty-text">{{ t('app.albums.empty') }}</p>
      <button class="btn-import">{{ t('app.albums.import_btn') }}</button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<style scoped>
.albums-page {
  padding: 2rem;
}
.albums-header {
  margin-bottom: 2rem;
}
.albums-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  text-align: center;
  color: var(--text-muted);
}
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-text { font-size: 1rem; margin-bottom: 1.5rem; }
.btn-import {
  padding: 0.6rem 1.5rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
}
.btn-import:hover { opacity: 0.9; }
</style>
