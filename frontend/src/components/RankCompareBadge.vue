<script setup lang="ts">
import { computed } from 'vue'
import CBadge from './ui/CBadge.vue'

const props = defineProps<{ section: string | number; rank: number }>()

const diff = computed(() => Number(props.section) - Number(props.rank))

// 差值语义：section > rank 表示该专业录取位次比用户靠后（更容易进，保底）→ teal
//          section < rank 表示录取位次比用户靠前（更难，冲刺）→ amber
const variant = computed(() => {
  const d = diff.value
  if (Math.abs(d) > 3000) return 'neutral'
  return d > 0 ? 'teal' : 'amber'
})

const label = computed(() => {
  const d = diff.value
  const sign = d > 0 ? '+' : ''
  return `Δ${sign}${d}`
})

const text = computed(() => {
  const d = diff.value
  if (Math.abs(d) > 3000) return '超筛选范围'
  return d > 0 ? '保底（你的位次更靠前）' : '冲刺（你的位次更靠后）'
})
</script>

<template>
  <span :title="text">
    <CBadge :variant="variant">{{ label }}</CBadge>
  </span>
</template>
