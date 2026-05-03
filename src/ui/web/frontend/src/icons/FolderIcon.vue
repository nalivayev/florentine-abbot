<template>
  <svg
    class="folder-icon"
    viewBox="0 0 24 24"
    fill="none"
    aria-hidden="true"
    :style="{ '--folder-icon-scale-x': horizontalScale }"
  >
    <path
      d="M3 7.25A2.25 2.25 0 0 1 5.25 5h4.16c.6 0 1.18.24 1.6.66l1.17 1.17c.42.42 1 .67 1.6.67h5.92A2.25 2.25 0 0 1 22 9.75v8A2.25 2.25 0 0 1 19.75 20h-14.5A2.25 2.25 0 0 1 3 17.75v-10.5Z"
      fill="currentColor"
      :fill-opacity="fillOpacity"
      stroke="currentColor"
      :stroke-width="strokeWidth"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup>
defineProps({
  strokeWidth: {
    type: [Number, String],
    default: 1.5,
  },
  fillOpacity: {
    type: [Number, String],
    default: 0.12,
  },
  horizontalScale: {
    type: [Number, String],
    default: 0.9,
  },
})
</script>

<style scoped>
.folder-icon {
  width: 100%;
  height: 100%;
  display: block;
  transform: scaleX(var(--folder-icon-scale-x, 0.9));
  transform-origin: center;
  transform-box: fill-box;
}
</style>