<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'cream' | 'canvas' }>(), { variant: 'cream' })
</script>

<template>
  <div class="c-card" :class="`c-card--${variant}`"><slot /></div>
</template>

<style scoped>
.c-card { border-radius: var(--r-card); padding: 32px; }
.c-card--cream { background: var(--c-surface-card); }
.c-card--canvas { background: var(--c-canvas); border: 1px solid var(--c-hairline); }
</style>
