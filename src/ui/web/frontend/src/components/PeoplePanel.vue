<template>
  <aside ref="rootEl" class="viewer-panel viewer-panel-people" :class="{ open }">
    <div v-if="faceCards.length === 0" class="viewer-people-placeholder">
      <p class="viewer-people-text">{{ emptyText }}</p>
    </div>

    <div v-else class="viewer-people-content">
      <div
        ref="listEl"
        class="viewer-people-list"
        :class="{
          'has-left-fade': hasLeftFade,
          'has-right-fade': hasRightFade,
        }"
        @scroll="$emit('scroll', $event)"
      >
        <button
          v-for="faceCard in faceCards"
          :key="faceCard.id"
          type="button"
          class="viewer-people-card"
          :data-face-id="String(faceCard.id)"
          :style="faceCard.cardStyle"
          @click="$emit('face-click', faceCard.face)"
          @mouseenter="$emit('face-enter', faceCard.face.id)"
          @mouseleave="$emit('face-leave')"
        >
          <span class="viewer-people-thumb">
            <img
              v-if="previewUrl"
              :src="previewUrl"
              alt=""
              class="viewer-people-thumb-image"
              :style="faceCard.imageStyle"
            >
            <span v-else class="viewer-people-thumb-placeholder">{{ faceCard.label }}</span>
            <span class="viewer-face-badge viewer-people-badge">{{ faceCard.label }}</span>
          </span>

          <span class="viewer-people-caption">
            <span class="viewer-people-name" :title="faceCard.name">{{ faceCard.name }}</span>
          </span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  open: { type: Boolean, default: false },
  faceCards: { type: Array, default: () => [] },
  previewUrl: { type: String, default: '' },
  hasLeftFade: { type: Boolean, default: false },
  hasRightFade: { type: Boolean, default: false },
  emptyText: { type: String, required: true },
})

defineEmits(['scroll', 'face-click', 'face-enter', 'face-leave'])

const rootEl = ref(null)
const listEl = ref(null)

defineExpose({ rootEl, listEl })
</script>

<style scoped>
.viewer-people-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.viewer-people-placeholder,
.viewer-people-thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}

.viewer-people-content,
.viewer-people-card,
.viewer-people-caption {
  display: flex;
  flex-direction: column;
}

.viewer-people-placeholder {
  min-height: 100%;
  padding: 0 var(--sp-4);
  text-align: center;
}

.viewer-people-text {
  margin: 0;
  max-width: 24rem;
  line-height: 1.55;
  color: var(--text-muted);
}

.viewer-people-content {
  min-height: 100%;
  gap: var(--sp-2);
}

.viewer-people-list {
  --viewer-people-fade-size: 1.5rem;
  --viewer-people-left-stop-1: #000 0;
  --viewer-people-left-stop-2: #000 0;
  --viewer-people-left-stop-3: #000 0;
  --viewer-people-left-stop-4: #000 0;
  --viewer-people-left-stop-5: #000 0;
  --viewer-people-right-stop-1: #000 100%;
  --viewer-people-right-stop-2: #000 100%;
  --viewer-people-right-stop-3: #000 100%;
  --viewer-people-right-stop-4: #000 100%;
  --viewer-people-right-stop-5: #000 100%;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 4.7rem;
  gap: var(--sp-3);
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: var(--sp-3);
  scrollbar-gutter: stable;
  align-items: start;
}

.viewer-people-list.has-left-fade {
  --viewer-people-left-stop-1: rgba(0, 0, 0, 0) 0;
  --viewer-people-left-stop-2: rgba(0, 0, 0, 0.18) calc(var(--viewer-people-fade-size) * 0.22);
  --viewer-people-left-stop-3: rgba(0, 0, 0, 0.52) calc(var(--viewer-people-fade-size) * 0.52);
  --viewer-people-left-stop-4: rgba(0, 0, 0, 0.86) calc(var(--viewer-people-fade-size) * 0.82);
  --viewer-people-left-stop-5: #000 var(--viewer-people-fade-size);
}

.viewer-people-list.has-right-fade {
  --viewer-people-right-stop-1: #000 calc(100% - var(--viewer-people-fade-size));
  --viewer-people-right-stop-2: rgba(0, 0, 0, 0.86) calc(100% - (var(--viewer-people-fade-size) * 0.82));
  --viewer-people-right-stop-3: rgba(0, 0, 0, 0.52) calc(100% - (var(--viewer-people-fade-size) * 0.52));
  --viewer-people-right-stop-4: rgba(0, 0, 0, 0.18) calc(100% - (var(--viewer-people-fade-size) * 0.22));
  --viewer-people-right-stop-5: rgba(0, 0, 0, 0) 100%;
}

.viewer-people-list.has-left-fade,
.viewer-people-list.has-right-fade {
  -webkit-mask-image: linear-gradient(
    to right,
    var(--viewer-people-left-stop-1),
    var(--viewer-people-left-stop-2),
    var(--viewer-people-left-stop-3),
    var(--viewer-people-left-stop-4),
    var(--viewer-people-left-stop-5),
    var(--viewer-people-right-stop-1),
    var(--viewer-people-right-stop-2),
    var(--viewer-people-right-stop-3),
    var(--viewer-people-right-stop-4),
    var(--viewer-people-right-stop-5)
  );
  mask-image: linear-gradient(
    to right,
    var(--viewer-people-left-stop-1),
    var(--viewer-people-left-stop-2),
    var(--viewer-people-left-stop-3),
    var(--viewer-people-left-stop-4),
    var(--viewer-people-left-stop-5),
    var(--viewer-people-right-stop-1),
    var(--viewer-people-right-stop-2),
    var(--viewer-people-right-stop-3),
    var(--viewer-people-right-stop-4),
    var(--viewer-people-right-stop-5)
  );
}

.viewer-people-list::-webkit-scrollbar {
  height: 0.35rem;
}

.viewer-people-list::-webkit-scrollbar-thumb {
  background: rgba(82, 92, 105, 0.46);
}

.viewer-people-card {
  --face-card-accent: #d19b2f;
  --face-card-fill: rgba(209, 155, 47, 0.14);
  --face-card-stroke-width: 1.5px;
  --face-card-tag-height: 20px;
  --face-card-tag-padding-x: 6px;
  gap: var(--sp-1-5);
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text);
  text-align: left;
  cursor: pointer;
  border-radius: var(--viewer-card-radius);
}

.viewer-people-thumb {
  position: relative;
  aspect-ratio: 4 / 5;
  box-sizing: border-box;
  overflow: hidden;
  border: var(--face-card-stroke-width) solid var(--face-card-accent);
  border-radius: var(--viewer-card-radius);
  background: var(--face-card-fill);
}

.viewer-people-thumb-image {
  position: absolute;
  max-width: none;
}

.viewer-people-thumb-placeholder {
  position: absolute;
  inset: 0;
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.viewer-face-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: var(--face-card-tag-height);
  min-width: 0;
  padding: 0 var(--face-card-tag-padding-x);
  box-sizing: border-box;
  font-family: "Segoe UI", sans-serif;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  color: #fff;
  background: var(--face-card-accent);
  border-radius: 0 0 var(--viewer-badge-radius) 0;
  white-space: nowrap;
}

.viewer-people-badge {
  position: absolute;
  top: 0;
  left: 0;
}

.viewer-people-caption {
  min-width: 0;
  gap: 1px;
  align-items: center;
  text-align: center;
}

.viewer-people-name {
  width: 100%;
  font-size: 12px;
  line-height: 1.1;
  font-weight: 400;
  color: var(--text);
}

[data-theme="dark"] .viewer-people-card {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.03);
}
</style>