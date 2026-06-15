<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'neutral' | 'coral' | 'success' | 'warning' | 'error' | 'teal' | 'amber'
}>(), { variant: 'neutral' })
</script>

<template>
  <span class="c-badge" :class="`c-badge--${variant}`"><slot /></span>
</template>

<style scoped>
.c-badge {
  display: inline-flex; align-items: center;
  font-size: 12px; font-weight: 500; letter-spacing: .2px;
  padding: 3px 10px; border-radius: var(--r-pill); white-space: nowrap;
}
.c-badge--neutral { background: var(--c-surface-card); color: var(--c-ink); }
.c-badge--coral { background: var(--c-primary); color: var(--c-on-primary); }
.c-badge--success { background: rgba(93, 184, 114, 0.16); color: #3f9a55; }
.c-badge--warning { background: rgba(212, 160, 23, 0.18); color: #9c7212; }
.c-badge--error { background: rgba(198, 69, 69, 0.16); color: var(--c-error); }
.c-badge--teal { background: rgba(93, 184, 166, 0.18); color: #2f8a78; }
.c-badge--amber { background: rgba(232, 165, 90, 0.22); color: #b9722f; }
</style>
