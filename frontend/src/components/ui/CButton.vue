<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost'
  disabled?: boolean
}>(), { variant: 'primary', disabled: false })
</script>

<template>
  <button
    class="c-btn"
    :class="[`c-btn--${variant}`, { 'is-disabled': disabled }]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<style scoped>
.c-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  height: 40px; padding: 0 20px;
  font-size: 14px; font-weight: 500; line-height: 1;
  border-radius: var(--r-control); border: 1px solid transparent;
  cursor: pointer; transition: background-color .15s, color .15s, border-color .15s;
  white-space: nowrap;
}
.c-btn--primary { background: var(--c-primary); color: var(--c-on-primary); }
.c-btn--primary:hover { background: var(--c-primary-active); }
.c-btn--secondary { background: var(--c-canvas); color: var(--c-ink); border-color: var(--c-hairline); }
.c-btn--secondary:hover { border-color: var(--c-muted-soft); }
.c-btn--ghost { background: transparent; color: var(--c-ink); }
.c-btn--ghost:hover { background: var(--c-surface-card); }
.is-disabled {
  background: var(--c-primary-disabled) !important;
  color: var(--c-muted) !important;
  cursor: not-allowed !important;
  border-color: transparent !important;
}
</style>
