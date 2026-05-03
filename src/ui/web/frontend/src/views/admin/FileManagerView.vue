<template>
  <div class="fm-page">
    <header class="fm-page-head">
      <div class="fm-page-copy">
        <h1 class="page-title">{{ t('file_manager.title') }}</h1>
        <p class="page-subtitle">{{ t('file_manager.subtitle') }}</p>
      </div>
    </header>

    <div class="fm-topbar">
      <nav class="fm-breadcrumb" aria-label="path">
        <button type="button" class="fm-crumb fm-crumb-root" @click="navigateTo('')">
          {{ t('file_manager.root') }}
        </button>
        <template v-for="(crumb, i) in breadcrumb" :key="crumb.path">
          <span class="fm-crumb-sep">/</span>
          <button
            type="button"
            class="fm-crumb"
            :class="{ active: i === breadcrumb.length - 1 }"
            @click="navigateTo(crumb.path)"
          >{{ crumb.name }}</button>
        </template>
      </nav>

      <div class="fm-topbar-actions">
        <button type="button" class="fm-btn fm-btn-secondary" @click="refreshCurrent">
          {{ t('file_manager.refresh') }}
        </button>
        <button type="button" class="fm-btn fm-btn-primary" @click="openCreateFolder">
          {{ t('file_manager.new_folder') }}
        </button>
        <button type="button" class="fm-btn fm-btn-danger" :disabled="!canOpenDeleteDialog" @click="openDeleteDialog">
          {{ t('file_manager.delete') }}
        </button>
      </div>
    </div>

    <div class="fm-workspace">
      <aside class="fm-tree-panel">
        <div class="fm-tree-head">
          <span class="fm-panel-title">{{ t('file_manager.folders_title') }}</span>
        </div>

        <div v-if="treeLoading" class="fm-state">{{ t('file_manager.loading') }}</div>
        <div v-else-if="treeError" class="fm-state fm-error">{{ treeError }}</div>
        <ul v-else class="fm-tree-root">
          <FolderNode
            v-for="node in tree"
            :key="node.path"
            :node="node"
            :selected-path="selectedPath"
            @select="navigateTo"
          />
        </ul>
      </aside>

      <section class="fm-list-panel">
        <div class="fm-browser-head">
          <div class="fm-browser-context">
            <span class="fm-panel-title">{{ t('file_manager.files_title') }}</span>
          </div>
          <div class="fm-browser-meta">
            <span class="fm-panel-meta">{{ t('file_manager.item_count') }}: {{ currentItemCount }}</span>
            <span v-if="selCount > 0" class="fm-panel-meta">{{ t('file_manager.selected', { n: selCount }) }}</span>
          </div>
        </div>

        <div v-if="filesLoading" class="fm-state">{{ t('file_manager.loading') }}</div>
        <div v-else-if="filesError" class="fm-state fm-error">{{ filesError }}</div>
        <div v-else-if="entries.length === 0" class="fm-state">{{ t('file_manager.empty') }}</div>
        <div v-else class="fm-list">
          <div class="fm-list-head">
            <span class="fm-col-check"></span>
            <span class="fm-col-media" aria-hidden="true"></span>
            <span class="fm-col-item">{{ t('file_manager.col_item') }}</span>
            <span class="fm-col-status">{{ t('file_manager.col_status') }}</span>
          </div>

          <div class="fm-list-body">
            <div
              v-for="entry in entries"
              :key="entry.key"
              class="fm-row"
              :class="{ selected: selectedItems.has(entry.key) }"
              @click="onEntryClick(entry, $event)"
              @dblclick="onEntryOpen(entry)"
            >
              <label class="fm-row-check" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedItems.has(entry.key)"
                  @change="toggleSelection(entry)"
                />
              </label>

              <div class="fm-row-media" :class="{ 'fm-row-media-folder': entry.kind === 'folder' }">
                <template v-if="entry.kind === 'file'">
                  <img
                    v-if="canPreview(entry) && !failedThumbs.has(entryPreviewKey(entry))"
                    :src="previewUrl(entry.id)"
                    class="fm-row-thumb"
                    :alt="entry.name"
                    @error="markThumbFailed(entryPreviewKey(entry))"
                  />
                  <div v-else class="fm-row-thumb-fallback">{{ fileExt(entry.name) }}</div>
                </template>
                <div v-else class="fm-row-folder-icon">
                  <FolderIcon
                    class="fm-row-folder-svg"
                    :stroke-width="0.6"
                    :fill-opacity="0.12"
                    :horizontal-scale="1"
                  />
                </div>
              </div>

              <div class="fm-row-main">
                <div class="fm-row-name-line">
                  <span class="fm-row-name">{{ entry.name }}</span>
                </div>
                <div v-if="entry.kind === 'file' && fileTrackingSummary(entry)" class="fm-row-subline">
                  {{ fileTrackingSummary(entry) }}
                </div>
              </div>

              <div class="fm-row-status">
                <span class="fm-badge" :class="entryStatusMeta(entry).badgeClass">{{ entryStatusMeta(entry).rowLabel }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <aside class="fm-details-panel fm-panel">
        <div class="fm-panel-head">
          <span class="fm-panel-title">{{ t('file_manager.details_title') }}</span>
        </div>

        <div class="fm-details-body">
          <template v-if="detailsFileSelection">
            <button
              type="button"
              class="fm-details-preview fm-details-preview-button"
              :class="{ 'is-disabled': !canPreview(detailsFileSelection) }"
              :aria-label="t('file_manager.open_preview')"
              :title="t('file_manager.open_preview')"
              :disabled="!canPreview(detailsFileSelection)"
              @click="openPreview(detailsFileSelection)"
            >
              <img
                v-if="canPreview(detailsFileSelection) && !failedThumbs.has(entryPreviewKey(detailsFileSelection))"
                :src="previewUrl(detailsFileSelection.id)"
                class="fm-details-image"
                :alt="detailsFileSelection.name"
                @error="markThumbFailed(entryPreviewKey(detailsFileSelection))"
              />
              <div v-else class="fm-details-placeholder">
                <span class="fm-details-placeholder-copy">{{ fileExt(detailsFileSelection.name) }}</span>
              </div>
            </button>

            <div class="fm-details-header-block">
              <p class="fm-details-name">{{ detailsFileSelection.name }}</p>
              <div class="fm-details-summary-line">
                <span v-if="detailsFileSelection.id != null" class="fm-details-token">
                  #{{ formatFileId(detailsFileSelection.id) }}
                </span>
                <span class="fm-badge" :class="entryStatusMeta(detailsFileSelection).badgeClass">
                  {{ entryStatusMeta(detailsFileSelection).rowLabel }}
                </span>
                <span class="fm-details-token">{{ formatSizeBytes(detailsFileSelection.sizeBytes) }}</span>
              </div>
            </div>

            <dl class="fm-details-meta fm-details-meta-compact">
              <div v-if="detailsFileSelection.id != null" class="fm-meta-row">
                <dt>{{ t('file_manager.col_collection') }}</dt>
                <dd>{{ detailsFileSelection.collectionName || t('file_manager.unassigned') }}</dd>
              </div>
              <div v-if="detailsFileSelection.importedAt" class="fm-meta-row">
                <dt>{{ t('file_manager.imported_at') }}</dt>
                <dd>{{ formatDateTime(detailsFileSelection.importedAt) }}</dd>
              </div>
              <div class="fm-meta-row">
                <dt>{{ t('file_manager.modified_at') }}</dt>
                <dd>{{ formatDateTime(detailsFileSelection.modifiedAt) }}</dd>
              </div>
              <div v-if="detailsFileSelection.creators.length > 0" class="fm-meta-row">
                <dt>{{ t('file_manager.creators') }}</dt>
                <dd>{{ detailsFileSelection.creators.join(', ') }}</dd>
              </div>
            </dl>

            <p v-if="selectedFileDetailLoading" class="fm-details-copy">{{ t('file_manager.loading') }}</p>
            <p v-else-if="selectedFileDetailError" class="fm-details-hint">{{ selectedFileDetailError }}</p>
          </template>

          <template v-else-if="primarySelection && primarySelection.kind === 'folder'">
            <div class="fm-details-preview" aria-hidden="true">
              <div class="fm-details-placeholder">
                <span class="fm-details-placeholder-copy">{{ t('file_manager.folder_badge') }}</span>
              </div>
            </div>

            <div class="fm-details-header-block">
              <p class="fm-details-name">{{ primarySelection.name }}</p>
              <div class="fm-details-summary-line">
                <span class="fm-badge" :class="entryStatusMeta(primarySelection).badgeClass">
                  {{ primarySelection.empty ? t('file_manager.folder_empty') : t('file_manager.folder_not_empty_state') }}
                </span>
                <span class="fm-details-token">{{ formatDateTime(primarySelection.modifiedAt) }}</span>
              </div>
            </div>

            <p v-if="isDeleteBlocked(primarySelection)" class="fm-details-hint">
              {{ t('file_manager.delete_disabled_non_empty_folder') }}
            </p>
          </template>

          <template v-else-if="selCount > 1">
            <p class="fm-details-copy">{{ selectionSummary }}</p>
            <p v-if="hasDeleteBlockedSelection" class="fm-details-hint">
              {{ t('file_manager.delete_disabled_selection_has_non_empty_folder') }}
            </p>
          </template>

          <template v-else>
            <p class="fm-details-name">{{ t('file_manager.current_folder_title') }}</p>
            <p class="fm-details-copy">{{ currentFolderLabel }}</p>

            <dl class="fm-details-meta">
              <div class="fm-meta-row">
                <dt>{{ t('file_manager.folders_title') }}</dt>
                <dd>{{ folders.length }}</dd>
              </div>
              <div class="fm-meta-row">
                <dt>{{ t('file_manager.files_title') }}</dt>
                <dd>{{ files.length }}</dd>
              </div>
            </dl>

            <p class="fm-details-hint">{{ t('file_manager.no_selection_hint') }}</p>
          </template>
        </div>
      </aside>
    </div>
  </div>

  <div v-if="confirmDelete" class="fm-overlay" @click.self="closeDeleteDialog">
    <div class="fm-dialog fm-dialog-delete">
      <div class="fm-dialog-body fm-dialog-delete-body">
        <div class="fm-dialog-header">
          <p class="fm-dialog-title">{{ t('file_manager.delete_title') }}</p>
          <p class="fm-dialog-text fm-dialog-lead">{{ t('file_manager.delete_confirm', { n: selCount }) }}</p>
        </div>

        <p class="fm-dialog-text fm-dialog-summary">{{ deleteSelectionSummary }}</p>
        <p class="fm-dialog-text fm-dialog-note">{{ t('file_manager.delete_task_note') }}</p>

        <div v-if="deletePreviewEntries.length">
          <div class="fm-dialog-section-head">
            <p class="fm-dialog-section">{{ t('file_manager.delete_list_title') }}</p>
            <p v-if="deletePreviewOverflow > 0" class="fm-dialog-caption">
              {{ t('file_manager.delete_more', { n: deletePreviewOverflow }) }}
            </p>
          </div>

          <ul class="fm-delete-list">
            <li v-for="entry in deletePreviewEntries" :key="entry.key" class="fm-delete-item">
              <div class="fm-delete-item-copy">
                <p class="fm-delete-item-name">{{ entry.name }}</p>
                <p class="fm-delete-item-path">{{ entry.path || t('file_manager.root') }}</p>
              </div>
            </li>
          </ul>
        </div>

        <p v-if="deleteError && !deleteFailures.length" class="fm-dialog-error">{{ deleteError }}</p>

        <div v-if="deleteFailures.length">
          <p v-if="deleteError" class="fm-dialog-error">{{ deleteError }}</p>
          <p v-else class="fm-dialog-text fm-dialog-feedback">{{ t('file_manager.delete_failures_title') }}</p>

          <ul class="fm-delete-list fm-delete-list-failures">
            <li v-for="failure in deleteFailures" :key="failure.key" class="fm-delete-item fm-delete-item-failure">
              <div class="fm-delete-item-copy">
                <p class="fm-delete-item-name">{{ failure.name }}</p>
                <p class="fm-delete-item-path">{{ failure.path || t('file_manager.root') }}</p>
                <p class="fm-delete-item-detail">{{ failure.detail }}</p>
              </div>
            </li>
          </ul>
        </div>

        <div class="fm-dialog-actions fm-dialog-actions-delete">
          <button type="button" class="fm-btn fm-btn-secondary" @click="closeDeleteDialog">
            {{ t('file_manager.cancel') }}
          </button>
          <button type="button" class="fm-btn fm-btn-danger" :disabled="deleting || !canOpenDeleteDialog" @click="doDelete">
            {{ deleting ? t('file_manager.loading') : t('file_manager.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <div v-if="showCreateFolder" class="fm-overlay" @click.self="showCreateFolder = false">
    <div class="fm-dialog">
      <div class="fm-dialog-body">
        <p class="fm-dialog-title">{{ t('file_manager.new_folder_title') }}</p>
        <input
          ref="folderNameInput"
          v-model="newFolderName"
          class="fm-input"
          :placeholder="t('file_manager.new_folder_placeholder')"
          @keydown.enter="doCreateFolder"
          @keydown.esc="showCreateFolder = false"
        />
        <p v-if="createError" class="fm-dialog-error">{{ createError }}</p>
        <div class="fm-dialog-actions">
          <button type="button" class="fm-btn fm-btn-secondary" @click="showCreateFolder = false">
            {{ t('file_manager.cancel') }}
          </button>
          <button type="button" class="fm-btn fm-btn-primary" :disabled="creatingFolder || !newFolderName.trim()" @click="doCreateFolder">
            {{ creatingFolder ? t('file_manager.loading') : t('file_manager.new_folder_btn') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiFetch, apiUrl } from '../../api.js'
import FolderNode from '../../components/admin/file-manager/FolderNode.vue'
import FolderIcon from '../../icons/FolderIcon.vue'

const { t, locale } = useI18n()

const tree = ref([])
const treeLoading = ref(true)
const treeError = ref('')

const folders = ref([])
const files = ref([])
const filesLoading = ref(false)
const filesError = ref('')

const selectedPath = ref('')
const selectedItems = ref(new Set())
const failedThumbs = ref(new Set())
const selectedFileDetail = ref(null)
const selectedFileDetailLoading = ref(false)
const selectedFileDetailError = ref('')

const confirmDelete = ref(false)
const deleting = ref(false)
const deleteError = ref('')
const deleteFailures = ref([])

const showCreateFolder = ref(false)
const newFolderName = ref('')
const creatingFolder = ref(false)
const createError = ref('')
const folderNameInput = ref(null)

let selectedFileDetailToken = 0

const selCount = computed(() => selectedItems.value.size)
const currentItemCount = computed(() => folders.value.length + files.value.length)
const currentFolderLabel = computed(() => {
  if (!selectedPath.value) return t('file_manager.root')
  return baseName(selectedPath.value)
})

const breadcrumb = computed(() => {
  if (!selectedPath.value) return []
  return selectedPath.value.split('/').map((part, i, arr) => ({
    name: part,
    path: arr.slice(0, i + 1).join('/'),
  }))
})

const entries = computed(() => [
  ...folders.value.map(folder => ({
    kind: 'folder',
    key: `folder:${folder.path}`,
    name: folder.name,
    path: folder.path,
    empty: Boolean(folder.empty),
    modifiedAt: folder.modified_at || null,
  })),
  ...files.value.map(file => {
    const tracked = normalizeTrackedFile(file)
    return {
      kind: 'file',
      key: tracked.id != null ? `file:${tracked.id}` : `file-path:${file.path}`,
      id: tracked.id,
      name: baseName(file.path),
      path: file.path,
      sizeBytes: typeof file.size_bytes === 'number' ? file.size_bytes : null,
      modifiedAt: file.modified_at || null,
      collectionId: tracked.collectionId,
      collectionName: tracked.collectionName,
      status: tracked.status,
      importedAt: tracked.importedAt,
      creators: [],
    }
  }),
])

const entryMap = computed(() => {
  const map = new Map()
  for (const entry of entries.value) map.set(entry.key, entry)
  return map
})

const selectedEntries = computed(() =>
  [...selectedItems.value]
    .map(key => entryMap.value.get(key))
    .filter(Boolean)
)

const primarySelection = computed(() =>
  selectedEntries.value.length === 1 ? selectedEntries.value[0] : null
)

const detailsFileSelection = computed(() => {
  if (!primarySelection.value || primarySelection.value.kind !== 'file') return null
  if (
    selectedFileDetail.value
    && selectedFileDetail.value.id != null
    && selectedFileDetail.value.id === primarySelection.value.id
  ) {
    return {
      ...primarySelection.value,
      ...selectedFileDetail.value,
    }
  }
  return primarySelection.value
})

const selectedFileCount = computed(() =>
  selectedEntries.value.filter(entry => entry.kind === 'file').length
)

const selectedFolderCount = computed(() =>
  selectedEntries.value.filter(entry => entry.kind === 'folder').length
)

const selectionSummary = computed(() =>
  t('file_manager.selection_summary', {
    total: selCount.value,
    files: selectedFileCount.value,
    folders: selectedFolderCount.value,
  })
)

const deletePreviewEntries = computed(() =>
  selectedEntries.value.slice(0, 6)
)

const deletePreviewOverflow = computed(() =>
  Math.max(0, selCount.value - deletePreviewEntries.value.length)
)

const deleteBlockedEntries = computed(() =>
  selectedEntries.value.filter(entry => isDeleteBlocked(entry))
)

const hasDeleteBlockedSelection = computed(() =>
  deleteBlockedEntries.value.length > 0
)

const canOpenDeleteDialog = computed(() =>
  selCount.value > 0 && !hasDeleteBlockedSelection.value
)

const deleteSelectionSummary = computed(() =>
  t('file_manager.delete_selection_summary', {
    total: selCount.value,
    files: selectedFileCount.value,
    folders: selectedFolderCount.value,
  })
)

function baseName(path) {
  return String(path).replace(/\\/g, '/').split('/').pop() || path
}

function normalizeTrackedFile(file) {
  return {
    id: typeof file?.id === 'number' ? file.id : null,
    collectionId: typeof file?.collection_id === 'number' ? file.collection_id : null,
    collectionName: typeof file?.collection_name === 'string' ? file.collection_name : '',
    status: typeof file?.status === 'string' && file.status ? file.status : 'untracked',
    importedAt: file?.imported_at || null,
  }
}

function normalizeTrackedFileDetail(file) {
  const tracked = normalizeTrackedFile(file)
  return {
    ...tracked,
    creators: Array.isArray(file?.creators)
      ? file.creators.filter(creator => typeof creator === 'string' && creator.trim())
      : [],
  }
}

function isTrackedFile(entry) {
  return entry?.kind === 'file' && entry.id != null
}

function fileExt(name) {
  const ext = String(name).split('.').pop()
  return ext ? ext.toUpperCase() : 'FILE'
}

function formatFileId(value) {
  return String(value).padStart(6, '0')
}

function fileStatusLabel(status) {
  const normalized = typeof status === 'string' && status ? status : 'untracked'
  switch (normalized) {
    case 'active':
    case 'new':
    case 'modified':
    case 'deleted':
    case 'untracked':
      return t(`file_manager.status.${normalized}`)
    default:
      return normalized
  }
}

function fileTrackingSummary(entry) {
  if (entry?.kind !== 'file') return ''
  if (!isTrackedFile(entry)) return fileStatusLabel('untracked')

  const parts = [`#${formatFileId(entry.id)}`]
  parts.push(entry.collectionName || t('file_manager.unassigned'))
  return parts.join(' · ')
}

function previewUrl(fileId) {
  return apiUrl(`/files/${fileId}/preview`)
}

function canPreview(entry) {
  return isTrackedFile(entry)
}

function entryPreviewKey(entry) {
  return entry?.id != null ? `file:${entry.id}` : `file-path:${entry?.path || ''}`
}

function entryStatusMeta(entry) {
  if (entry.kind === 'folder') {
    return {
      label: t('file_manager.folder_badge'),
      rowLabel: entry.empty ? t('file_manager.folder_empty') : t('file_manager.folder_not_empty_state'),
      badgeClass: 'fm-badge-folder',
    }
  }

  const status = isTrackedFile(entry) ? entry.status : 'untracked'
  const badgeClassByStatus = {
    active: 'fm-badge-active',
    new: 'fm-badge-new',
    modified: 'fm-badge-modified',
    deleted: 'fm-badge-deleted',
    untracked: 'fm-badge-muted',
  }

  return {
    label: t('file_manager.file_badge'),
    rowLabel: fileStatusLabel(status),
    badgeClass: badgeClassByStatus[status] || 'fm-badge-unknown',
  }
}

function formatSizeBytes(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return '—'
  if (value < 1024) return `${value} B`

  const units = ['KB', 'MB', 'GB', 'TB']
  let size = value / 1024
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unitIndex]}`
}

function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(locale.value, { dateStyle: 'short', timeStyle: 'short' })
}

function markThumbFailed(fileId) {
  const next = new Set(failedThumbs.value)
  next.add(fileId)
  failedThumbs.value = next
}

function isDeleteBlocked(entry) {
  return entry.kind === 'folder' && !entry.empty
}

function resetDeleteFeedback() {
  deleteError.value = ''
  deleteFailures.value = []
}

function openDeleteDialog() {
  if (!canOpenDeleteDialog.value) return
  resetDeleteFeedback()
  confirmDelete.value = true
}

function closeDeleteDialog() {
  if (deleting.value) return
  confirmDelete.value = false
  resetDeleteFeedback()
}

function translateDeleteDetail(detail) {
  switch (detail) {
    case 'Folder is not empty':
      return t('file_manager.delete_reason_folder_not_empty')
    case 'Archive not configured':
      return t('file_manager.delete_reason_archive_not_configured')
    case 'path is required':
      return t('file_manager.delete_reason_invalid_path')
    case 'Not Found':
      return t('file_manager.delete_reason_not_found')
    default:
      return detail || t('file_manager.delete_error')
  }
}

async function getDeleteErrorDetail(res) {
  const data = await res.json().catch(() => ({}))
  return translateDeleteDetail(data.detail || `${res.status} ${res.statusText}`)
}

function clearSelection() {
  selectedItems.value = new Set()
}

function toggleSelection(entry) {
  const next = new Set(selectedItems.value)
  if (next.has(entry.key)) next.delete(entry.key)
  else next.add(entry.key)
  selectedItems.value = next
}

function onEntryClick(entry, event) {
  if (event.ctrlKey || event.metaKey) {
    toggleSelection(entry)
    return
  }

  if (selectedItems.value.size === 1 && selectedItems.value.has(entry.key)) {
    clearSelection()
    return
  }

  selectedItems.value = new Set([entry.key])
}

function onEntryOpen(entry) {
  if (entry.kind === 'folder') {
    void navigateTo(entry.path)
    return
  }
  openPreview(entry)
}

function openPreview(entry) {
  if (!canPreview(entry)) return
  window.open(previewUrl(entry.id), '_blank', 'noopener')
}

async function loadFolder(path) {
  filesLoading.value = true
  filesError.value = ''
  try {
    const res = await apiFetch(`/files/browse?path=${encodeURIComponent(path)}`)
    if (!res.ok) {
      filesError.value = `${res.status} ${res.statusText}`
      folders.value = []
      files.value = []
      return
    }
    const data = await res.json()
    folders.value = data.folders || []
    files.value = data.files || []
  } catch (error) {
    filesError.value = String(error)
    folders.value = []
    files.value = []
  } finally {
    filesLoading.value = false
  }
}

async function loadSelectedFileDetail(entry) {
  if (!isTrackedFile(entry)) {
    selectedFileDetailToken += 1
    selectedFileDetail.value = null
    selectedFileDetailLoading.value = false
    selectedFileDetailError.value = ''
    return
  }

  const token = ++selectedFileDetailToken
  selectedFileDetailLoading.value = true
  selectedFileDetailError.value = ''
  selectedFileDetail.value = null

  try {
    const res = await apiFetch(`/files/${entry.id}`)
    if (token !== selectedFileDetailToken) return
    if (!res.ok) {
      selectedFileDetailError.value = `${res.status} ${res.statusText}`
      return
    }

    const data = await res.json()
    if (token !== selectedFileDetailToken) return
    selectedFileDetail.value = normalizeTrackedFileDetail(data)
  } catch (error) {
    if (token !== selectedFileDetailToken) return
    selectedFileDetailError.value = String(error)
  } finally {
    if (token === selectedFileDetailToken) {
      selectedFileDetailLoading.value = false
    }
  }
}

async function navigateTo(path) {
  selectedPath.value = path || ''
  clearSelection()
  await loadFolder(selectedPath.value)
}

async function loadTree() {
  treeLoading.value = true
  treeError.value = ''
  try {
    const res = await apiFetch('/files/tree')
    if (!res.ok) {
      treeError.value = `${res.status} ${res.statusText}`
      tree.value = []
      return
    }
    tree.value = await res.json()
  } catch (error) {
    treeError.value = String(error)
    tree.value = []
  } finally {
    treeLoading.value = false
  }
}

async function refreshCurrent() {
  await Promise.all([loadTree(), loadFolder(selectedPath.value)])
}

function openCreateFolder() {
  newFolderName.value = ''
  createError.value = ''
  showCreateFolder.value = true
  nextTick(() => folderNameInput.value?.focus())
}

async function doCreateFolder() {
  const name = newFolderName.value.trim()
  if (!name) return
  creatingFolder.value = true
  createError.value = ''
  try {
    const folderPath = selectedPath.value ? `${selectedPath.value}/${name}` : name
    const res = await apiFetch('/folders', {
      method: 'POST',
      body: { path: folderPath },
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      createError.value = data.detail || t('file_manager.new_folder_error')
      return
    }
    showCreateFolder.value = false
    newFolderName.value = ''
    await refreshCurrent()
  } catch {
    createError.value = t('file_manager.new_folder_error')
  } finally {
    creatingFolder.value = false
  }
}

async function doDelete() {
  if (deleting.value || !canOpenDeleteDialog.value) return

  const selection = [...selectedEntries.value]
  const byKey = new Map(selection.map(entry => [entry.key, entry]))
  const fileIds = selection
    .filter(entry => entry.kind === 'file' && entry.id != null)
    .map(entry => entry.id)
  const filePaths = selection
    .filter(entry => entry.kind === 'file' && entry.id == null)
    .map(entry => entry.path)
  const folderPaths = selection.filter(entry => entry.kind === 'folder').map(entry => entry.path)

  deleting.value = true
  resetDeleteFeedback()
  try {
    const res = await apiFetch('/files/delete', {
      method: 'POST',
      body: {
        files: fileIds,
        file_paths: filePaths,
        folders: folderPaths,
      },
    })

    if (!res.ok) {
      deleteError.value = await getDeleteErrorDetail(res)
      return
    }

    const data = await res.json()
    const failed = (data.failed || []).map(failure => ({
      ...(byKey.get(failure.key) || { key: failure.key, name: failure.key, path: '' }),
      detail: translateDeleteDetail(failure.detail),
    }))

    await refreshCurrent()

    if (failed.length > 0) {
      deleteFailures.value = failed
      deleteError.value = t('file_manager.delete_failed_summary', {
        failed: failed.length,
        total: selection.length,
      })
      selectedItems.value = new Set(failed.map(entry => entry.key))
      return
    }

    confirmDelete.value = false
    resetDeleteFeedback()
    clearSelection()
  } catch {
    deleteError.value = t('file_manager.delete_error')
  } finally {
    deleting.value = false
  }
}

watch(entries, (nextEntries) => {
  const validKeys = new Set(nextEntries.map(entry => entry.key))
  const filtered = [...selectedItems.value].filter(key => validKeys.has(key))
  if (filtered.length !== selectedItems.value.size) {
    selectedItems.value = new Set(filtered)
  }
}, { deep: true })

watch(
  () => primarySelection.value?.key || null,
  () => {
    if (!primarySelection.value || primarySelection.value.kind !== 'file') {
      void loadSelectedFileDetail(null)
      return
    }
    void loadSelectedFileDetail(primarySelection.value)
  },
)

onMounted(async () => {
  await Promise.all([loadTree(), loadFolder(selectedPath.value)])
})
</script>

<style scoped>
.fm-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  min-height: 100%;
}

.fm-page-head {
  min-width: 0;
}

.fm-page-copy .page-subtitle {
  margin-bottom: 0;
}

.fm-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: 0;
}

.fm-breadcrumb {
  display: flex;
  align-items: center;
  gap: 2px;
  min-width: 0;
  overflow: hidden;
}

.fm-crumb {
  background: none;
  border: none;
  padding: 2px var(--sp-1);
  font-size: var(--fs-sm);
  line-height: 1;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-xs);
  white-space: nowrap;
}

.fm-crumb:hover { color: var(--text); background: var(--surface-muted); }
.fm-crumb.active { color: var(--text-muted); cursor: default; }
.fm-crumb.active:hover { background: none; }
.fm-crumb-root { color: var(--accent); }
.fm-crumb-root:hover { color: var(--accent); }
.fm-crumb-sep { color: var(--border); font-size: var(--fs-sm); user-select: none; }

.fm-topbar-actions,
.fm-dialog-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.fm-details-copy,
.fm-details-hint,
.fm-panel-meta {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--fs-sm);
}

.fm-workspace {
  display: grid;
  grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr) 22rem;
  gap: var(--sp-3);
  min-height: 0;
  flex: 1;
  align-items: stretch;
}

.fm-panel {
  display: flex;
  flex-direction: column;
  min-height: 34rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  overflow: hidden;
}

.fm-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--border);
}

.fm-panel-title {
  color: var(--text-heading);
  font-size: var(--fs-sm);
  font-weight: 600;
}

.fm-tree-panel,
.fm-list-panel,
.fm-details-panel {
  min-height: 0;
}

.fm-tree-panel,
.fm-list-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 34rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.fm-tree-panel {
  background: var(--surface);
  border-color: color-mix(in srgb, var(--border) 88%, var(--accent) 12%);
}

.fm-list-panel {
  background: var(--surface);
}

.fm-tree-head,
.fm-browser-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--border);
}

.fm-tree-head {
  background: var(--surface);
}

.fm-browser-head {
  background: var(--surface);
}

.fm-browser-context {
  min-width: 0;
  display: flex;
  flex: 1;
}

.fm-browser-path {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fm-browser-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-left: auto;
  flex-shrink: 0;
  gap: var(--sp-3);
  flex-wrap: nowrap;
  text-align: right;
  white-space: nowrap;
}

.fm-tree-root {
  list-style: none;
  margin: 0;
  padding: var(--sp-2) var(--sp-4) var(--sp-4);
  overflow: auto;
  overflow-x: hidden;
  flex: 1;
  background: var(--surface);
}

.fm-state {
  padding: var(--sp-5) var(--sp-4);
  color: var(--text-muted);
  font-size: var(--fs-sm);
}

.fm-error { color: var(--danger); }

.fm-list {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
  min-width: 0;
}

.fm-list-head,
.fm-row {
  display: grid;
  grid-template-columns: 2.25rem 3.75rem minmax(12rem, 1fr) 8rem;
  gap: var(--sp-3);
  align-items: center;
}

.fm-list-head {
  padding: var(--sp-2) var(--sp-4);
  color: var(--text-muted);
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border);
}

.fm-list-body {
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
  min-width: 0;
}

.fm-row {
  padding: var(--sp-2) var(--sp-4);
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background var(--motion-base), border-color var(--motion-base);
}

.fm-row:last-child {
  border-bottom: none;
}

.fm-row:hover {
  background: var(--surface-muted);
}

.fm-row.selected {
  background: var(--bg-accent);
}

.fm-row-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.fm-row-check input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.fm-row-media {
  width: 3.75rem;
  height: 3.75rem;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-muted);
  display: flex;
  align-items: center;
  justify-content: center;
}

.fm-row-media-folder {
  background: transparent;
}

.fm-row-thumb,
.fm-details-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.fm-row-thumb-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--bg-accent), var(--surface-muted));
  color: var(--accent);
  font-size: var(--fs-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
}

.fm-row-folder-icon,
.fm-details-folder-mark {
  color: var(--accent);
}

.fm-row-folder-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fm-row-folder-svg {
  width: 98%;
  height: 98%;
}

.fm-row-main {
  min-width: 0;
}

.fm-row-name-line {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: 4px;
}

.fm-row-name,
.fm-details-name {
  color: var(--text-heading);
  font-size: var(--fs-sm);
  font-weight: 600;
}

.fm-details-name {
  margin: 0;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.fm-row-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fm-row-subline {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fm-badge {
  display: inline-flex;
  align-items: center;
  border-radius: var(--radius-pill);
  padding: var(--inset-pill-y) var(--inset-pill-x);
  font-size: var(--fs-2xs);
  font-weight: 600;
  white-space: nowrap;
}

.fm-badge-folder {
  color: var(--accent);
  background: var(--bg-accent);
  border: 1px solid var(--border-accent);
}

.fm-badge-neutral {
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
}

.fm-badge-muted {
  color: var(--text-muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
}

.fm-badge-warning {
  color: var(--warning);
  background: var(--bg-warning);
  border: 1px solid var(--border-warning);
}

.fm-badge-active {
  color: var(--success);
  background: var(--bg-success);
  border: 1px solid var(--border-success);
}

.fm-badge-new,
.fm-badge-modified {
  color: var(--warning);
  background: var(--bg-warning);
  border: 1px solid var(--border-warning);
}

.fm-badge-deleted,
.fm-badge-unknown {
  color: var(--danger);
  background: var(--bg-danger);
  border: 1px solid var(--border-danger);
}

.fm-row-status {
  color: var(--text);
  font-size: var(--fs-sm);
  min-width: 0;
}

.fm-row-dash {
  color: var(--text-muted);
}

.fm-details-body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-4);
  overflow-y: auto;
  min-height: 0;
}

.fm-details-preview {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-muted);
}

.fm-details-preview-button {
  appearance: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-align: inherit;
  box-shadow: inset 0 0 0 1px transparent;
  transition: box-shadow var(--motion-base);
}

.fm-details-preview-button:hover {
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 35%, transparent);
}

.fm-details-preview-button.is-disabled,
.fm-details-preview-button:disabled {
  cursor: default;
  box-shadow: none;
}

.fm-details-preview-button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.fm-details-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--bg-accent), var(--surface-muted));
  color: var(--accent);
}

.fm-details-placeholder-copy {
  display: block;
  max-width: 78%;
  color: var(--accent);
  font-size: var(--fs-base);
  font-weight: 600;
  letter-spacing: 0.08em;
  line-height: 1.2;
  text-align: center;
  text-wrap: balance;
}

.fm-details-header-block {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.fm-details-summary-line {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.fm-details-token {
  display: inline-flex;
  align-items: center;
  min-height: 1.5rem;
  padding: 0 var(--sp-2);
  border-radius: var(--radius-pill);
  background: var(--surface-muted);
  color: var(--text);
  font-size: var(--fs-xs);
  font-weight: 600;
  white-space: nowrap;
}

.fm-details-meta {
  display: grid;
  gap: var(--sp-3);
  margin: 0;
}

.fm-details-meta-compact {
  gap: var(--sp-3);
}

.fm-meta-row {
  display: grid;
  gap: 2px;
}

.fm-meta-row dt {
  color: var(--text-muted);
  font-size: var(--fs-2xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.fm-meta-row dd {
  margin: 0;
  color: var(--text);
  font-size: var(--fs-sm);
  overflow-wrap: anywhere;
}

.fm-details-state {
  padding: 0;
}

.fm-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
}

.fm-dialog {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  max-width: 30rem;
  width: calc(100% - var(--sp-8));
  box-shadow: var(--shadow-elevated);
}

.fm-dialog-delete {
  max-width: 42rem;
  max-height: calc(100vh - var(--sp-10));
}

.fm-dialog-body { padding: var(--sp-5); }

.fm-dialog-delete-body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.fm-dialog-header {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.fm-dialog-title {
  margin: 0;
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-heading);
}

.fm-dialog-section {
  margin: 0 0 var(--sp-2);
  font-size: var(--fs-xs);
  color: var(--text-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.fm-dialog-text {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--text-muted);
}

.fm-dialog-lead {
  max-width: 42ch;
}

.fm-dialog-summary {
  color: var(--text-heading);
  font-weight: 600;
}

.fm-dialog-note {
  font-size: var(--fs-xs);
}

.fm-dialog-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-2);
}

.fm-delete-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: var(--sp-3);
  overflow: auto;
  max-height: min(18rem, 42vh);
}

.fm-delete-item {
  padding: 0;
  background: transparent;
}

.fm-delete-item-failure {
  color: inherit;
}

.fm-delete-item-copy {
  min-width: 0;
}

.fm-delete-item-name {
  margin: 0 0 4px;
  color: var(--text-heading);
  font-size: var(--fs-sm);
  font-weight: 600;
  overflow-wrap: anywhere;
}

.fm-delete-item-path {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--fs-xs);
  overflow-wrap: anywhere;
}

.fm-delete-item-detail {
  margin: var(--sp-2) 0 0;
  color: var(--danger);
  font-size: var(--fs-xs);
  overflow-wrap: anywhere;
}

.fm-dialog-caption,
.fm-dialog-feedback {
  margin: 0;
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.fm-delete-list-failures {
  margin-top: var(--sp-2);
}

.fm-dialog-error {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--danger);
}

.fm-dialog-actions-delete {
  justify-content: flex-end;
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
}

.fm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-1);
  min-height: 2.25rem;
  padding: 0 var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity var(--motion-base), background var(--motion-base), border-color var(--motion-base);
}

.fm-btn:disabled {
  opacity: 0.55;
  cursor: default;
}

.fm-btn-secondary {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
}

.fm-btn-secondary:hover:not(:disabled) {
  background: var(--surface-muted);
}

.fm-btn-primary {
  background: var(--accent);
  border: 1px solid var(--accent);
  color: #fff;
}

.fm-btn-primary:hover:not(:disabled),
.fm-btn-danger:hover:not(:disabled) {
  opacity: 0.88;
}

.fm-btn-danger {
  background: var(--danger);
  border: 1px solid var(--danger);
  color: #fff;
}

.fm-input {
  width: 100%;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: var(--fs-sm);
  margin-bottom: var(--sp-4);
}

.fm-input:focus {
  outline: none;
  border-color: var(--accent);
}

@media (max-width: 1200px) {
  .fm-workspace {
    grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr);
  }

  .fm-details-panel {
    grid-column: 1 / -1;
  }
}

@media (max-width: 980px) {
  .fm-workspace {
    grid-template-columns: 1fr;
  }

  .fm-details-panel {
    grid-column: auto;
  }

  .fm-tree-panel {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}

@media (max-width: 860px) {
  .fm-topbar {
    flex-direction: column;
    align-items: stretch;
  }

  .fm-dialog-delete {
    width: calc(100% - var(--sp-4));
  }

  .fm-list-head,
  .fm-row {
    grid-template-columns: 2rem 4.25rem minmax(0, 1fr);
  }

  .fm-col-status,
  .fm-row-status {
    display: none;
  }
}
</style>
