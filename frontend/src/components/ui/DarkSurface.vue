<script setup lang="ts">
// 深色产品卡 —— 用于展示真实数据（进度面板、回归方程、位次分布），符合 Claude「深色产品卡承载真实数据」原则。
</script>

<template>
  <div class="dark-surface"><slot /></div>
</template>

<style scoped>
.dark-surface {
  background: var(--c-surface-dark);
  color: var(--c-on-dark);
  border-radius: var(--r-card);
  padding: 32px;
}
.dark-surface :deep(.muted) { color: var(--c-on-dark-soft); }
</style>
