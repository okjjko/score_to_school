<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TaskConfig } from '../api/endpoints'
import DarkSurface from './ui/DarkSurface.vue'
import CBadge from './ui/CBadge.vue'
import CButton from './ui/CButton.vue'
import CProgress from './ui/CProgress.vue'
import { useTaskStore } from '../stores/task'

const props = defineProps<{ taskResumeCfg?: TaskConfig | null }>()
const emit = defineEmits<{ 'view-results': [] }>()

const task = useTaskStore()
const p = computed(() => task.current)

const phaseLabel = computed(() => {
  const phase = p.value?.phase
  if (phase === 'sleeping') return '反爬冷却中'
  if (phase === 'retry') return '触发风控，重试等待中'
  if (phase === 'done') return '已完成'
  return '抓取中'
})

const phaseVariant = computed(() => {
  const phase = p.value?.phase
  if (phase === 'retry') return 'error' as const
  if (phase === 'sleeping') return 'warning' as const
  if (phase === 'done') return 'success' as const
  return 'teal' as const
})

const statusLabel = computed(() => {
  const s = p.value?.status
  const map: Record<string, string> = {
    running: '运行中', pausing: '暂停中', paused: '已暂停',
    cancelling: '取消中', cancelled: '已取消',
    interrupted: '已中断（服务端重启）',
    done: '已完成', error: '出错',
  }
  return map[s || ''] || s || ''
})

const etaText = computed(() => {
  const c = p.value
  if (!c || !c.processed || c.processed < 5 || !c.total) return null
  // 粗估：假设每校约 8 秒（含随机延迟与偶发冷却）
  const remaining = c.total - c.processed
  const secs = remaining * 8
  if (secs > 3600) return `预计还需约 ${Math.round(secs / 3600)} 小时`
  if (secs > 60) return `预计还需约 ${Math.round(secs / 60)} 分钟`
  return `预计还需约 ${secs} 秒`
})

function onResume() {
  if (props.taskResumeCfg) task.start(props.taskResumeCfg)
}

const pausing = ref(false)
const cancelling = ref(false)
async function onPause() {
  if (pausing.value) return
  pausing.value = true
  try { await task.pause() } catch {}
}
async function onCancel() {
  if (cancelling.value) return
  cancelling.value = true
  try { await task.cancel() } catch {}
}
</script>

<template>
  <DarkSurface>
    <div class="flex items-center justify-between flex-wrap gap-3 mb-6">
      <div class="flex items-center gap-3">
        <CBadge :variant="phaseVariant">{{ phaseLabel }}</CBadge>
        <span class="status-text">{{ statusLabel }}</span>
      </div>
      <span class="muted mono-sm">任务 · {{ p?.task_id }}</span>
    </div>

    <!-- 进度条 + 计数 -->
    <div class="mb-2 flex items-baseline justify-between">
      <span class="big-num">{{ p?.processed || 0 }}<span class="muted"> / {{ p?.total || 0 }}</span></span>
      <span class="muted">{{ task.pct }}%</span>
    </div>
    <CProgress :pct="task.pct" variant="dark" />

    <div class="metrics">
      <div class="metric">
        <div class="muted metric-label">已匹配学校</div>
        <div class="metric-val accent">{{ p?.matched || 0 }}</div>
      </div>
      <div class="metric">
        <div class="muted metric-label">当前学校</div>
        <div class="metric-val school" :title="p?.school || ''">{{ p?.school || '—' }}</div>
      </div>
      <div class="metric">
        <div class="muted metric-label">{{ (p?.phase === 'sleeping' || p?.phase === 'retry') ? '剩余等待' : '预计剩余' }}</div>
        <div class="metric-val">
          <span v-if="p?.phase === 'sleeping' || p?.phase === 'retry'">{{ p?.remaining_sec || 0 }} 秒</span>
          <span v-else>{{ etaText || '估算中…' }}</span>
        </div>
      </div>
    </div>

    <div v-if="p?.error" class="error-box">{{ p.error }}</div>

    <!-- 中断提示：服务端重启后任务停止，可从断点继续 -->
    <div v-if="p?.status === 'interrupted'" class="info-box">
      服务端已重启，任务在此停止。点击「恢复抓取」将从上次断点（已处理 {{ p?.processed || 0 }} 所学校）继续。
    </div>

    <!-- 操作 -->
    <div class="actions" v-if="p?.status !== 'done' && p?.status !== 'error' && p?.status !== 'cancelled'">
      <CButton v-if="p?.status === 'paused' || p?.status === 'interrupted'" variant="primary" @click="onResume">恢复抓取</CButton>
      <CButton v-if="p?.status !== 'interrupted'" variant="secondary-dark" :disabled="pausing" @click="onPause">
        {{ pausing ? '暂停中…' : '暂停' }}
      </CButton>
      <CButton variant="ghost-dark" :disabled="cancelling" @click="onCancel">
        {{ cancelling ? '取消中…' : '取消任务' }}
      </CButton>
    </div>
    <div v-else-if="p?.status === 'done'" class="done-box">
      <CButton variant="primary" @click="emit('view-results')">查看结果</CButton>
    </div>
  </DarkSurface>
</template>

<style scoped>
.muted { color: var(--c-on-dark-soft); }
.status-text { font-size: 14px; color: var(--c-on-dark); }
.mono-sm { font-size: 12px; font-family: 'JetBrains Mono', monospace; }

.big-num {
  font-family: 'Cormorant Garamond', 'Noto Serif SC', serif;
  font-size: 40px; font-weight: 400; color: var(--c-on-dark); line-height: 1;
}
.big-num .muted { font-size: 22px; }

.metrics {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 28px;
}
.metric-label { font-size: 12px; margin-bottom: 6px; }
.metric-val { font-size: 18px; font-weight: 500; color: var(--c-on-dark); }
.metric-val.school { font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.metric-val.accent { color: var(--c-primary); }

.error-box {
  margin-top: 20px; padding: 12px 16px; border-radius: var(--r-control);
  background: rgba(198, 69, 69, 0.15); color: #f0a0a0; font-size: 14px;
  font-family: 'JetBrains Mono', monospace;
}

.info-box {
  margin-top: 20px; padding: 12px 16px; border-radius: var(--r-control);
  background: rgba(204, 120, 92, 0.18); color: #f0c8b8; font-size: 14px;
  line-height: 1.6;
}

.actions { display: flex; gap: 12px; margin-top: 28px; flex-wrap: wrap; }
.done-box { margin-top: 28px; }

@media (max-width: 640px) {
  .metrics { grid-template-columns: 1fr; gap: 16px; }
}
</style>
