<script setup lang="ts">
defineProps<{
  tabs: { key: string; label: string }[]
  modelValue: string
}>()
defineEmits<{ 'update:modelValue': [v: string] }>()
</script>

<template>
  <div class="c-tabs">
    <button
      v-for="t in tabs"
      :key="t.key"
      class="c-tab"
      :class="{ active: t.key === modelValue }"
      @click="$emit('update:modelValue', t.key)"
    >{{ t.label }}</button>
  </div>
</template>

<style scoped>
.c-tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--c-hairline); overflow-x: auto; }
.c-tab {
  background: transparent; color: var(--c-muted); border: none;
  font-size: 14px; font-weight: 500; padding: 12px 16px; cursor: pointer;
  position: relative; white-space: nowrap; transition: color .15s;
}
.c-tab:hover { color: var(--c-ink); }
.c-tab.active { color: var(--c-ink); }
.c-tab.active::after {
  content: ''; position: absolute; left: 16px; right: 16px; bottom: -1px;
  height: 2px; background: var(--c-primary);
}
</style>
