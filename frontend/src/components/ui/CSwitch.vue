<script setup lang="ts">
defineProps<{ modelValue: boolean; label?: string }>()
defineEmits<{ 'update:modelValue': [v: boolean] }>()
</script>

<template>
  <label class="c-switch">
    <span class="c-switch__track" :class="{ on: modelValue }">
      <input
        type="checkbox"
        :checked="modelValue"
        @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      />
      <span class="c-switch__thumb"></span>
    </span>
    <span v-if="label" class="c-switch__label">{{ label }}</span>
  </label>
</template>

<style scoped>
.c-switch { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; }
.c-switch__track {
  width: 40px; height: 22px; border-radius: var(--r-pill);
  background: var(--c-surface-cream-strong); position: relative;
  transition: background .15s; flex-shrink: 0;
}
.c-switch__track.on { background: var(--c-primary); }
.c-switch__track input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
.c-switch__thumb {
  position: absolute; top: 3px; left: 3px; width: 16px; height: 16px;
  border-radius: 50%; background: var(--c-surface-dark-elevated);
  transition: transform .15s, background .15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
}
.c-switch__track.on .c-switch__thumb { transform: translateX(18px); background: var(--c-on-primary); }
.c-switch__label { font-size: 14px; color: var(--c-ink); }
</style>
