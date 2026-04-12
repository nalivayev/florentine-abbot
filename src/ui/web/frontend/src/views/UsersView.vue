<template>
  <h1 class="page-title">{{ t('users.title') }}</h1>
  <p class="page-subtitle">{{ t('users.subtitle') }}</p>

  <div class="users-body">

    <!-- User list -->
    <table class="users-table" v-if="users.length">
      <thead>
        <tr>
          <th>{{ t('users.col_username') }}</th>
          <th>{{ t('users.col_role') }}</th>
          <th>{{ t('users.col_last_login') }}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id" :class="{ 'row-self': u.id === currentUserId }">
          <td class="col-username">{{ u.username }}</td>
          <td><span class="role-badge" :class="`role-${u.role}`">{{ t(`users.role_${u.role}`) }}</span></td>
          <td class="col-muted">{{ u.last_login_at ? formatDate(u.last_login_at) : '—' }}</td>
          <td class="col-actions">
            <button
              v-if="u.id !== currentUserId"
              class="btn-remove"
              @click="confirmDelete(u)"
            >{{ t('users.delete') }}</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Add user form -->
    <div class="add-section">
      <p class="subsection-label">{{ t('users.add_title') }}</p>
      <div class="add-form">
        <input
          class="field-input"
          v-model="form.username"
          :placeholder="t('users.username_placeholder')"
          @keydown.enter="addUser"
        />
        <input
          class="field-input"
          v-model="form.password"
          type="password"
          :placeholder="t('users.password_placeholder')"
          @keydown.enter="addUser"
        />
        <select class="field-input" v-model="form.role">
          <option value="user">{{ t('users.role_user') }}</option>
          <option value="admin">{{ t('users.role_admin') }}</option>
        </select>
        <button class="btn btn-save" @click="addUser" :disabled="adding">
          {{ t('users.add_btn') }}
        </button>
      </div>
      <p v-if="formError" class="form-error">{{ formError }}</p>
    </div>

  </div>

  <!-- Delete confirm dialog -->
  <ConfirmDialog
    :visible="!!deleteTarget"
    :title="t('users.confirm_delete_title')"
    :message="t('users.confirm_delete_message', { name: deleteTarget?.username })"
    :confirmLabel="t('users.delete')"
    @confirm="doDelete"
    @cancel="deleteTarget = null"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiFetch } from '../api.js'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const { t, locale } = useI18n()

const users = ref([])
const currentUserId = ref(null)
const deleteTarget = ref(null)
const adding = ref(false)
const formError = ref('')

const form = ref({ username: '', password: '', role: 'user' })

async function fetchUsers() {
  const res = await apiFetch('/users')
  users.value = await res.json()
}

async function fetchMe() {
  const res = await apiFetch('/auth/me')
  if (res.ok) currentUserId.value = (await res.json()).id
}

onMounted(() => Promise.all([fetchUsers(), fetchMe()]))

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(locale.value, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function confirmDelete(u) {
  deleteTarget.value = u
}

async function doDelete() {
  await apiFetch(`/users/${deleteTarget.value.id}`, { method: 'DELETE' })
  deleteTarget.value = null
  await fetchUsers()
}

async function addUser() {
  formError.value = ''
  if (!form.value.username.trim() || !form.value.password.trim()) {
    formError.value = t('setup.validation.required')
    return
  }
  adding.value = true
  try {
    const res = await apiFetch('/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    if (!res.ok) {
      const d = await res.json()
      const key = `users.error_${d.detail}`
      formError.value = t(key) !== key ? t(key) : d.detail
      return
    }
    form.value = { username: '', password: '', role: 'user' }
    await fetchUsers()
  } finally {
    adding.value = false
  }
}
</script>

<style scoped>
.users-body { max-width: 640px; }
.users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm);
  margin-bottom: var(--sp-7);
}
.users-table th {
  text-align: left;
  font-size: var(--fs-xs);
  font-weight: 600;
  color: var(--text-muted);
  padding: 0 var(--sp-3) var(--sp-2);
  border-bottom: 1px solid var(--border);
}
.users-table td {
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--border);
  color: var(--text);
}
.users-table tr:last-child td { border-bottom: none; }
.row-self td { color: var(--text-muted); }
.col-username { font-weight: 500; }
.col-muted { color: var(--text-muted); font-size: var(--fs-xs); }
.col-actions { text-align: right; }
.role-badge {
  display: inline-block;
  padding: 0.1rem var(--sp-2);
  border-radius: 3px;
  font-size: var(--fs-xs);
  font-weight: 500;
}
.role-admin { background: var(--bg-accent); color: var(--accent); }
.role-user  { background: var(--surface-muted); color: var(--text-muted); }
.btn-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: var(--fs-xs);
  cursor: pointer;
  padding: 0;
}
.btn-remove:hover { color: var(--danger); }
.subsection-label {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text);
  margin: 0 0 var(--sp-3);
}
.add-form {
  display: flex;
  gap: var(--sp-2);
  align-items: center;
  flex-wrap: wrap;
}
.add-form .field-input { flex: 1; min-width: 120px; }
.add-section { margin-top: var(--sp-2); }
.form-error {
  margin-top: var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--danger);
}
</style>
