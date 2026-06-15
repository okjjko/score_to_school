<script setup lang="ts">
withDefaults(defineProps<{
  pct: number
  variant?: 'light' | 'dark'
}>(), { variant: 'light' })
</script>

<template>
  <div class="c-progress" :class="`c-progress--${variant}`">
    <div class="c-progress__fill" :style="{ width: Math.min(100, Math.max(0, pct)) + '%' }"></div>
  </div>
</template>

<style scoped>
.c-progress { height: 8px; border-radius: var(--r-pill); overflow: hidden; width: 100%; }
.c-progress--light { background: var(--c-surface-cream-strong); }
.c-progress--dark { background: var(--c-surface-dark-soft); }
.c-progress__fill {
  height: 100%; background: var(--c-primary);
  border-radius: var(--r-pill); transition: width .4s ease;
}
</style>
