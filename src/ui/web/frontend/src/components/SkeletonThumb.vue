<template>
  <div class="skeleton-thumb">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <circle cx="12" cy="12" r="9"/>
      <polyline points="12 7 12 12 15 15"/>
    </svg>
  </div>
</template>

<style scoped>
.skeleton-thumb {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-muted);
  animation: skeleton-pulse 2s ease-in-out infinite;
}
.skeleton-thumb svg {
  width: 2rem;
  height: 2rem;
  color: var(--text-muted);
  opacity: 0.5;
}
@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
