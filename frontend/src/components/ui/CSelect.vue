<script setup lang="ts">
defineProps<{
  modelValue: string | number
  label?: string
  options: { value: string | number; label: string }[]
}>()
defineEmits<{ 'update:modelValue': [v: string] }>()
</script>

<template>
  <label class="c-field">
    <span v-if="label" class="c-field__label">{{ label }}</span>
    <select
      class="c-select"
      :value="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
    </select>
  </label>
</template>

<style scoped>
.c-field { display: flex; flex-direction: column; gap: 6px; }
.c-field__label { font-size: 13px; font-weight: 500; color: var(--c-muted); }
.c-select {
  height: 40px; padding: 0 32px 0 14px;
  background-color: var(--c-canvas); color: var(--c-ink);
  border: 1px solid var(--c-hairline); border-radius: var(--r-control);
  font-size: 15px; font-family: inherit; outline: none; cursor: pointer;
  appearance: none; -webkit-appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236c6a64' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'/></svg>");
  background-repeat: no-repeat; background-position: right 12px center;
  transition: border-color .15s, box-shadow .15s; width: 100%;
}
.c-select:focus { border-color: var(--c-primary); box-shadow: 0 0 0 3px rgba(204, 120, 92, 0.15); }
</style>
