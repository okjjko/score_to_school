<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConfigStore } from '../stores/config'
import { useTaskStore } from '../stores/task'
import type { TaskConfig } from '../api/endpoints'
import CCard from '../components/ui/CCard.vue'
import CInput from '../components/ui/CInput.vue'
import CSelect from '../components/ui/CSelect.vue'
import CSwitch from '../components/ui/CSwitch.vue'
import CButton from '../components/ui/CButton.vue'
import CBadge from '../components/ui/CBadge.vue'
import ProgressPanel from '../components/ProgressPanel.vue'

const router = useRouter()
const configStore = useConfigStore()
const task = useTaskStore()

const SUBJECT_OPTIONS = ['物理', '化学', '生物', '政治', '历史', '地理']

// 表单内部统一用 string（select/input 原生值），提交时转 number
const form = ref({
  province_id: '52',
  rank: '12000',
  want: '生物科学',
  year: '2024',
  ethnic_minority: false,
  subject: ['物理', '化学', '生物'] as string[],
  thread_num: '2',
})

const provinceOptions = computed(() =>
  (configStore.provinces || []).map(p => ({ value: String(p.id), label: `${p.name}（${p.id}）` }))
)

const cfg = computed<TaskConfig>(() => ({
  province_id: Number(form.value.province_id),
  rank: Number(form.value.rank),
  want: form.value.want.trim(),
  year: Number(form.value.year),
  ethnic_minority: form.value.ethnic_minority,
  output: 'json',
  subject: form.value.subject,
  thread_num: Number(form.value.thread_num),
}))

const showProgress = computed(() => task.current !== null)
const starting = ref(false)
const errorMsg = ref('')

// 续传用 cfg：优先取后端从 task_state 带回的原始 cfg（用户可能已改表单，
// interrupted/paused 恢复必须用任务当初的参数，否则 task_id 不一致无法命中 progress.db）
const resumeCfg = computed<TaskConfig>(() => task.current?.cfg || cfg.value)

onMounted(async () => {
  await configStore.load()
  if (configStore.config) {
    const c = configStore.config
    form.value = {
      province_id: String(c.province_id),
      rank: String(c.rank),
      want: c.want,
      year: String(c.year),
      ethnic_minority: c.ethnic_minority,
      subject: c.subject || [],
      thread_num: String(c.thread_num),
    }
  }
})

function toggleSubject(s: string) {
  const arr = form.value.subject
  const i = arr.indexOf(s)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(s)
}

async function startScrape() {
  errorMsg.value = ''
  if (!form.value.want.trim()) { errorMsg.value = '请填写专业关键字'; return }
  if (!form.value.rank || Number(form.value.rank) <= 0) { errorMsg.value = '请填写有效位次'; return }
  starting.value = true
  try {
    await configStore.save(cfg.value)
    await task.start(cfg.value)
  } catch (e) {
    errorMsg.value = (e as Error).message || '启动失败'
  } finally {
    starting.value = false
  }
}

function viewResults() {
  router.push('/results')
}
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="hero">
      <p class="t-caption-uppercase text-muted mb-3">配置与抓取</p>
      <h1 class="hero-title">筛选你的目标院校</h1>
      <p class="hero-sub text-muted">
        输入省份、专业关键字与你的位次，从全国高校录取数据中筛选位次差小于 3000 的匹配项。
      </p>
      <div class="hero-meta" v-if="configStore.schoolsCount">
        <CBadge variant="coral">将扫描 {{ configStore.schoolsCount.total }} 所高校</CBadge>
        <CBadge variant="neutral">其中约 {{ configStore.schoolsCount.usable }} 所参与匹配</CBadge>
      </div>
    </section>

    <div class="grid">
      <!-- 配置表单 -->
      <CCard variant="cream">
        <h2 class="section-title">抓取参数</h2>
        <div class="form-grid">
          <CSelect v-model="form.province_id" label="省份" :options="provinceOptions" />
          <CInput v-model="form.year" label="年份" type="number" />
          <CInput v-model="form.want" label="专业关键字" placeholder="如 生物科学" />
          <CInput v-model="form.rank" label="你的位次" type="number" />
          <CInput v-model="form.thread_num" label="线程数" type="number" />
          <div class="field">
            <span class="field-label">少数民族（含专项计划）</span>
            <CSwitch v-model="form.ethnic_minority" />
          </div>
        </div>

        <div class="field mt-4">
          <span class="field-label">选考科目（记录用，暂不影响筛选）</span>
          <div class="chips">
            <button
              v-for="s in SUBJECT_OPTIONS"
              :key="s"
              class="chip"
              :class="{ active: form.subject.includes(s) }"
              @click="toggleSubject(s)"
            >{{ s }}</button>
          </div>
        </div>

        <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

        <div class="cta-row">
          <CButton variant="primary" :disabled="starting || task.isRunning || task.resuming" @click="startScrape">
            {{ starting ? '启动中…' : '开始抓取' }}
          </CButton>
          <span class="hint text-muted">单任务可能运行数小时（反爬限速），可随时暂停与续传。</span>
        </div>
      </CCard>

      <!-- 进度面板 -->
      <div v-if="showProgress" class="progress-col">
        <ProgressPanel :task-resume-cfg="resumeCfg" @view-results="viewResults" />
      </div>
      <!-- 未抓取时的占位引导（深色卡，呼应 hero 节奏） -->
      <div v-else class="progress-col">
        <div class="idle-card">
          <p class="t-caption-uppercase muted mb-3">实时进度</p>
          <p class="muted">填写参数后点击「开始抓取」，这里会以深色面板实时展示当前学校、已匹配数、反爬冷却与风控重试状态。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero { margin-bottom: 48px; max-width: 720px; }
.hero-title { font-size: 48px; line-height: 1.1; letter-spacing: -1px; }
.hero-sub { margin-top: 16px; font-size: 16px; }
.hero-meta { margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap; }
.text-muted { color: var(--c-muted); }

.grid { display: grid; grid-template-columns: 1fr; gap: 32px; align-items: start; }
@media (min-width: 960px) { .grid { grid-template-columns: 1fr 1fr; } }

.section-title { font-size: 22px; margin-bottom: 24px; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 600px) { .form-grid { grid-template-columns: 1fr; } }

.field { display: flex; flex-direction: column; gap: 8px; }
.field-label { font-size: 13px; font-weight: 500; color: var(--c-muted); }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  padding: 6px 14px; border-radius: var(--r-pill); border: 1px solid var(--c-hairline);
  background: var(--c-canvas); color: var(--c-body); font-size: 13px; cursor: pointer;
  transition: background-color .15s, color .15s, border-color .15s;
}
.chip:hover { border-color: var(--c-muted-soft); }
.chip.active { background: var(--c-primary); color: var(--c-on-primary); border-color: var(--c-primary); }

.mt-4 { margin-top: 16px; }
.error { color: var(--c-error); font-size: 14px; margin-top: 16px; }

.cta-row { margin-top: 28px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.hint { font-size: 13px; }

.progress-col { min-width: 0; }
.idle-card {
  background: var(--c-surface-dark); color: var(--c-on-dark-soft);
  border-radius: var(--r-card); padding: 32px;
}
.idle-card .muted { color: var(--c-on-dark-soft); font-size: 15px; line-height: 1.6; }
</style>
