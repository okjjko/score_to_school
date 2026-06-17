<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, type ResumeItem, type ResultFile, type TaskSummary } from '../api/endpoints'
import { useTaskStore } from '../stores/task'
import CCard from '../components/ui/CCard.vue'
import CButton from '../components/ui/CButton.vue'
import CBadge from '../components/ui/CBadge.vue'

const router = useRouter()
const task = useTaskStore()

const resumes = ref<ResumeItem[]>([])
// 进程内可恢复任务（interrupted=服务端重启、paused=手动暂停）；含完整 cfg，可一键起线程续传
const liveTasks = ref<TaskSummary[]>([])
const files = ref<ResultFile[]>([])
const provinceMap = ref<Record<string, string>>({})

function provName(id: string | number) {
  return provinceMap.value[String(id)] || String(id)
}
function fmtTime(ts: number) {
  const d = new Date(ts * 1000)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

async function refresh() {
  resumes.value = await api.listResume()
  files.value = await api.listResults()
  // 只展示可恢复态（interrupted/paused）；running 由配置页进度面板处理
  try {
    const all = await api.listTasks()
    liveTasks.value = all.filter((t) => t.status === 'interrupted' || t.status === 'paused')
  } catch {
    liveTasks.value = []
  }
}

// 恢复进程内可恢复任务：用 task_state 带回的完整 cfg 重新起线程（process 自动读 progress.db 续传）
async function resumeLiveTask(item: TaskSummary) {
  if (!item.cfg) return
  try {
    await task.start(item.cfg)
    router.push('/')
  } catch {
    /* 409 等情况忽略，停留本页 */
  }
}

async function resumeTask(item: ResumeItem) {
  // 续传参数写入 config.json，配置页加载时会预填；用户确认后点「开始抓取」即从断点继续
  await api.putConfig({
    province_id: Number(item.province_id),
    rank: item.rank,
    want: item.want,
    year: item.year,
    ethnic_minority: false,
    output: 'json',
    subject: [],
    thread_num: 2,
  })
  task.reset()
  router.push('/')
}

async function delResume(taskId: string) {
  if (!confirm('确定删除这条续传记录吗？已抓取的中间结果将丢失。')) return
  await api.deleteResume(taskId)
  await refresh()
}

function openResult(f: ResultFile) {
  router.push({ path: '/results', query: { file: f.file } })
}

onMounted(async () => {
  const provs = await api.getProvinces()
  provinceMap.value = Object.fromEntries(provs.map(p => [String(p.id), p.name]))
  await refresh()
})
</script>

<template>
  <div>
    <section class="hero">
      <p class="t-caption-uppercase text-muted mb-3">历史与续传</p>
      <h1 style="font-size: 40px;">断点续传与历史结果</h1>
      <p class="text-muted mt-2">未完成的抓取任务可从此处恢复；历史结果文件可重新打开查看。</p>
    </section>

    <!-- 可恢复任务（服务端重启后中断 / 手动暂停；含完整参数，一键续传） -->
    <template v-if="liveTasks.length">
      <h2 class="section-title">可恢复任务</h2>
      <div class="resume-list">
        <div v-for="t in liveTasks" :key="t.task_id" class="resume-item">
          <div class="resume-info">
            <div class="resume-title">{{ t.cfg?.want }}</div>
            <div class="text-muted resume-sub mono">{{ provName(t.cfg?.province_id || '') }} · {{ t.cfg?.year }} · 位次 {{ t.cfg?.rank }}</div>
            <div class="resume-badges">
              <CBadge variant="warning">{{ t.status === 'interrupted' ? '服务端重启中断' : '已暂停' }}</CBadge>
              <CBadge variant="teal">已处理 {{ t.processed }}</CBadge>
              <CBadge v-if="t.matched" variant="coral">已匹配 {{ t.matched }}</CBadge>
            </div>
          </div>
          <div class="resume-actions">
            <CButton variant="primary" @click="resumeLiveTask(t)">恢复</CButton>
          </div>
        </div>
      </div>
    </template>

    <!-- 断点续传 -->
    <h2 class="section-title">断点续传</h2>
    <CCard v-if="!resumes.length" variant="canvas">
      <p class="text-muted">暂无未完成的任务。抓取过程中断（或手动暂停）后，会在这里出现可恢复的记录。</p>
    </CCard>
    <div v-else class="resume-list">
      <div v-for="r in resumes" :key="r.task_id" class="resume-item">
        <div class="resume-info">
          <div class="resume-title">{{ r.want }}</div>
          <div class="text-muted resume-sub mono">{{ provName(r.province_id) }} · {{ r.year }} · 位次 {{ r.rank }}</div>
          <div class="resume-badges">
            <CBadge variant="teal">已处理 {{ r.processed_count }}</CBadge>
            <CBadge variant="coral">已匹配 {{ r.results_count }}</CBadge>
          </div>
        </div>
        <div class="resume-actions">
          <CButton variant="primary" @click="resumeTask(r)">恢复</CButton>
          <CButton variant="ghost" @click="delResume(r.task_id)">删除</CButton>
        </div>
      </div>
      <p class="hint text-muted">恢复后将跳转配置页，请确认「少数民族」等参数后开始（已处理学校会自动跳过）。</p>
    </div>

    <!-- 历史结果 -->
    <h2 class="section-title" style="margin-top: 48px;">历史结果</h2>
    <CCard v-if="!files.length" variant="canvas">
      <p class="text-muted">暂无结果文件。完成一次抓取后会在这里生成。</p>
    </CCard>
    <div v-else class="result-grid">
      <button v-for="f in files" :key="f.file" class="result-card" @click="openResult(f)">
        <span class="t-caption-uppercase text-muted">年份</span>
        <span class="rc-year">{{ f.year }}</span>
        <span class="rc-want">{{ f.want }}</span>
        <span class="text-muted rc-meta">{{ f.size_kb }} KB · {{ fmtTime(f.mtime) }}</span>
        <span class="rc-arrow">查看 →</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.text-muted { color: var(--c-muted); }
.mono { font-family: 'JetBrains Mono', monospace; }
.hero { margin-bottom: 32px; }

.section-title { font-size: 22px; margin-bottom: 20px; }

.resume-list { display: flex; flex-direction: column; gap: 12px; }
.resume-item {
  display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  background: var(--c-surface-card); border-radius: var(--r-card); padding: 20px 24px;
}
.resume-title { font-family: 'Cormorant Garamond', 'Noto Serif SC', serif; font-size: 22px; color: var(--c-ink); }
.resume-sub { font-size: 13px; margin-top: 4px; }
.resume-badges { display: flex; gap: 8px; margin-top: 12px; }
.resume-actions { display: flex; gap: 10px; }
.hint { font-size: 13px; margin-top: 12px; }

.result-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.result-card {
  display: flex; flex-direction: column; gap: 6px; text-align: left;
  background: var(--c-canvas); border: 1px solid var(--c-hairline); border-radius: var(--r-card);
  padding: 24px; cursor: pointer; transition: border-color .15s, transform .15s;
  font-family: inherit;
}
.result-card:hover { border-color: var(--c-primary); transform: translateY(-2px); }
.rc-year { font-family: 'Cormorant Garamond', 'Noto Serif SC', serif; font-size: 36px; color: var(--c-ink); line-height: 1; }
.rc-want { font-size: 16px; font-weight: 500; color: var(--c-ink); }
.rc-meta { font-size: 13px; }
.rc-arrow { color: var(--c-primary); font-size: 14px; font-weight: 500; margin-top: 8px; }
</style>
