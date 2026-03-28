<template>
  <div class="login-wrap">
    <div class="login-box">
      <h1>{{ t('login.title') }}</h1>
      <form @submit.prevent="submit">
        <div class="field">
          <label>{{ t('login.username') }}</label>
          <input v-model="username" type="text" autocomplete="username" required />
        </div>
        <div class="field">
          <label>{{ t('login.password') }}</label>
          <input v-model="password" type="password" autocomplete="current-password" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ t('login.submit') }}</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiUrl } from '../api.js'

const { t } = useI18n()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await fetch(apiUrl('/auth/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    if (!res.ok) {
      const data = await res.json()
      error.value = data.detail || t('login.error_invalid')
      return
    }
    const data = await res.json()
    localStorage.setItem('token', data.token)
    if (window.location.pathname.startsWith('/admin')) {
      router.push('/admin/config')
    } else {
      router.push('/albums')
    }
  } catch {
    error.value = t('login.error_unavailable')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
}
.login-box {
  width: 320px;
}
h1 {
  font-size: var(--fs-lg);
  font-weight: 600;
  color: var(--text);
  margin-bottom: var(--sp-7);
}
.field {
  margin-bottom: var(--sp-4);
}
label {
  display: block;
  font-size: var(--fs-sm);
  color: var(--text-muted);
  margin-bottom: 0.35rem;
}
input {
  width: 100%;
  padding: var(--sp-2) 0.6rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-base);
  box-sizing: border-box;
}
input:focus {
  outline: none;
  border-color: var(--accent);
}
button {
  width: 100%;
  margin-top: var(--sp-2);
  padding: 0.55rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: var(--fs-base);
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
.error {
  font-size: var(--fs-sm);
  color: var(--danger);
  margin: var(--sp-2) 0;
}
</style>
