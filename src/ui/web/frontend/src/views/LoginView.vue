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
    router.push('/admin/tasks/organizer')
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
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 2rem;
}
.field {
  margin-bottom: 1rem;
}
label {
  display: block;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.35rem;
}
input {
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
button {
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.55rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
.error {
  font-size: 0.82rem;
  color: var(--danger);
  margin: 0.5rem 0;
}
</style>
