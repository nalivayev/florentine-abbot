<template>
  <li class="fn-item">
    <button
      type="button"
      class="fn-row"
      :class="{ selected: node.path === selectedPath }"
      @click="toggle"
    >
      <svg v-if="node.children.length > 0" class="fn-arrow" :class="{ open: isOpen }" viewBox="0 0 16 16" fill="none">
        <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span v-else class="fn-arrow-spacer" />
      <FolderIcon class="fn-icon" :stroke-width="1.25" :fill-opacity="0" />
      <span class="fn-name">{{ node.name }}</span>
    </button>

    <ul v-if="isOpen && node.children.length > 0" class="fn-children">
      <FolderNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :selected-path="selectedPath"
        @select="$emit('select', $event)"
      />
    </ul>
  </li>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import FolderIcon from '../../../icons/FolderIcon.vue'
import FolderNode from './FolderNode.vue'

const props = defineProps({
  node: { type: Object, required: true },
  selectedPath: { type: String, default: '' },
})

const emit = defineEmits(['select'])
const isOpen = ref(false)

const isActiveBranch = computed(() => {
  if (!props.selectedPath) return false
  return props.selectedPath === props.node.path || props.selectedPath.startsWith(`${props.node.path}/`)
})

watch(isActiveBranch, (active) => {
  if (active) isOpen.value = true
}, { immediate: true })

function toggle() {
  if (props.node.children.length > 0) {
    isOpen.value = props.node.path === props.selectedPath ? !isOpen.value : true
  }
  emit('select', props.node.path)
}
</script>

<style scoped>
.fn-item { list-style: none; }

.fn-row {
  position: relative;
  z-index: 0;
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  width: 100%;
  padding: 5px var(--sp-2);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
  color: var(--text);
  font-size: var(--fs-sm);
}
.fn-row::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  border-radius: inherit;
  transition: background var(--motion-base);
}
.fn-row:hover::before { background: var(--surface-muted); }
.fn-row.selected { color: var(--accent); }
.fn-row.selected::before { background: var(--bg-accent); }

.fn-arrow {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  color: var(--text-muted);
  transition: transform var(--motion-base);
}
.fn-arrow.open { transform: rotate(90deg); }
.fn-arrow-spacer { width: 12px; height: 12px; flex-shrink: 0; display: inline-block; }

.fn-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: var(--accent);
}

.fn-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fn-children {
  list-style: none;
  margin: 0;
  padding: 0 0 0 var(--sp-4);
}
</style>
