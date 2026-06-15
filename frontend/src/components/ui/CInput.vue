<script setup lang="ts">
defineProps<{
  modelValue: string | number
  label?: string
  placeholder?: string
  type?: string
}>()
defineEmits<{ 'update:modelValue': [v: string] }>()
</script>

<template>
  <label class="c-field">
    <span v-if="label" class="c-field__label">{{ label }}</span>
    <input
      class="c-input"
      :type="type || 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
  </label>
</template>

<style scoped>
.c-field { display: flex; flex-direction: column; gap: 6px; }
.c-field__label { font-size: 13px; font-weight: 500; color: var(--c-muted); }
.c-input {
  height: 40px; padding: 0 14px;
  background: var(--c-canvas); color: var(--c-ink);
  border: 1px solid var(--c-hairline); border-radius: var(--r-control);
  font-size: 15px; font-family: inherit; outline: none;
  transition: border-color .15s, box-shadow .15s; width: 100%;
}
.c-input::placeholder { color: var(--c-muted-soft); }
.c-input:focus { border-color: var(--c-primary); box-shadow: 0 0 0 3px rgba(204, 120, 92, 0.15); }
</style>
