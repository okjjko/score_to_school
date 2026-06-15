<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { api, type ResultFile, type SchoolResult } from '../api/endpoints'
import CTabs from '../components/ui/CTabs.vue'
import CBadge from '../components/ui/CBadge.vue'
import DarkSurface from '../components/ui/DarkSurface.vue'
import RankCompareBadge from '../components/RankCompareBadge.vue'

interface Major { name: string; min: string | number; min_section: string | number }
interface School { name: string; majors: Major[]; minSection: number }

function flatten(data: SchoolResult): School[] {
  return data.map(item => {
    const name = Object.keys(item)[0]
    const arr = item[name] as unknown as Record<string, { min: string | number; min_section: string | number }>[]
    const majors: Major[] = arr.map(m => {
      const spname = Object.keys(m)[0]
      return { name: spname, min: m[spname].min, min_section: m[spname].min_section }
    })
    const minSection = majors.length ? Math.min(...majors.map(m => Number(m.min_section))) : 0
    return { name, majors, minSection }
  })
}

const files = ref<ResultFile[]>([])
const activeFile = ref('')
const rawData = ref<SchoolResult>([])
const rank = ref(12000)
const sortKey = ref<'diff' | 'section' | 'name'>('diff')
const expanded = ref<Set<string>>(new Set())
const loading = ref(false)

const fileTabs = computed(() => files.value.map(f => ({ key: f.file, label: `${f.want} · ${f.year}` })))

const schools = computed(() => {
  const list = flatten(rawData.value)
  list.sort((a, b) => {
    if (sortKey.value === 'diff') return Math.abs(a.minSection - rank.value) - Math.abs(b.minSection - rank.value)
    if (sortKey.value === 'section') return a.minSection - b.minSection
    return a.name.localeCompare(b.name, 'zh')
  })
  return list
})

const totalMajors = computed(() => schools.value.reduce((s, x) => s + x.majors.length, 0))

function toggle(name: string) {
  const s = new Set(expanded.value)
  s.has(name) ? s.delete(name) : s.add(name)
  expanded.value = s
}

async function loadFile() {
  if (!activeFile.value) return
  loading.value = true
  try {
    rawData.value = await api.readResult(activeFile.value)
    expanded.value = new Set()
  } finally {
    loading.value = false
  }
}

watch(activeFile, () => { loadFile().then(updateChart) })

// 位次差分布直方图
const chartEl = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const route = useRoute()

function chartOption() {
  const counts = new Array(8).fill(0)
  for (const s of flatten(rawData.value)) {
    for (const m of s.majors) {
      const d = Number(m.min_section) - rank.value
      if (d <= -3000) counts[0]++
      else if (d <= -2000) counts[1]++
      else if (d <= -1000) counts[2]++
      else if (d <= 0) counts[3]++
      else if (d <= 1000) counts[4]++
      else if (d <= 2000) counts[5]++
      else if (d <= 3000) counts[6]++
      else counts[7]++
    }
  }
  const buckets = ['≤-3000', '-3000', '-2000', '-1000', '0', '1000', '2000', '≥3000']
  return {
    grid: { left: 44, right: 16, top: 16, bottom: 48 },
    tooltip: { trigger: 'axis', backgroundColor: '#252320', borderColor: '#252320', textStyle: { color: '#faf9f5' } },
    xAxis: {
      type: 'category', data: buckets,
      axisLabel: { color: '#a09d96', fontSize: 11 },
      axisLine: { lineStyle: { color: '#252320' } }, axisTick: { show: false },
    },
    yAxis: {
      type: 'value', minInterval: 1,
      axisLabel: { color: '#a09d96' },
      splitLine: { lineStyle: { color: '#252320' } },
    },
    series: [{
      type: 'bar', data: counts, barWidth: '60%',
      itemStyle: { color: '#cc785c', borderRadius: [4, 4, 0, 0] },
    }],
  }
}

async function updateChart() {
  if (!chart) return
  chart.setOption(chartOption())
}

function onResize() { chart?.resize() }

onMounted(async () => {
  files.value = await api.listResults()
  try {
    const cfg = await api.getConfig()
    rank.value = cfg.rank
  } catch { /* ignore */ }
  const qf = route.query.file ? String(route.query.file) : ''
  if (qf && files.value.some(f => f.file === qf)) {
    activeFile.value = qf
  } else if (files.value.length) {
    activeFile.value = files.value[0].file
  }
  if (activeFile.value) await loadFile()
  await nextTick()
  if (chartEl.value) {
    chart = echarts.init(chartEl.value)
    chart.setOption(chartOption())
  }
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<template>
  <div>
    <section class="hero">
      <p class="t-caption-uppercase text-muted mb-3">结果</p>
      <h1 style="font-size: 40px;">录取分数结果</h1>
      <p class="text-muted mt-2">按你的位次（<span class="mono">{{ rank }}</span>）展示匹配的学校与专业，位次差越小越接近你的水平。</p>
    </section>

    <div v-if="!files.length" class="empty">
      <p class="text-muted">暂无结果文件。请先到「配置与抓取」运行一次抓取。</p>
    </div>

    <template v-else>
      <!-- 文件选择 -->
      <CTabs :tabs="fileTabs" v-model="activeFile" />

      <div class="summary" v-if="rawData.length">
        <CBadge variant="coral">{{ schools.length }} 所学校</CBadge>
        <CBadge variant="neutral">{{ totalMajors }} 个专业</CBadge>
      </div>

      <!-- 排序控件 -->
      <div class="sort-row" v-if="rawData.length">
        <span class="text-muted sort-label">排序</span>
        <button class="sort-btn" :class="{ active: sortKey === 'diff' }" @click="sortKey = 'diff'">位次差</button>
        <button class="sort-btn" :class="{ active: sortKey === 'section' }" @click="sortKey = 'section'">录取位次</button>
        <button class="sort-btn" :class="{ active: sortKey === 'name' }" @click="sortKey = 'name'">学校名</button>
      </div>

      <!-- 学校列表 -->
      <div class="school-list" v-if="rawData.length">
        <div v-for="s in schools" :key="s.name" class="school">
          <div class="school-head" @click="toggle(s.name)">
            <span class="expand-icon" :class="{ open: expanded.has(s.name) }">›</span>
            <div class="school-main">
              <span class="school-name">{{ s.name }}</span>
              <span class="text-muted school-sub">{{ s.majors.length }} 个匹配专业</span>
            </div>
            <div class="school-meta">
              <span class="mono section-num">{{ s.minSection }}</span>
              <RankCompareBadge :section="s.minSection" :rank="rank" />
            </div>
          </div>

          <div v-if="expanded.has(s.name)" class="major-list">
            <div v-for="m in s.majors" :key="m.name" class="major">
              <div class="major-name">{{ m.name }}</div>
              <div class="major-stats">
                <span class="mono">最低分 {{ m.min }}</span>
                <span class="mono">位次 {{ m.min_section }}</span>
                <RankCompareBadge :section="m.min_section" :rank="rank" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 位次差分布（深色产品卡） -->
      <DarkSurface v-if="rawData.length" >
        <p class="t-caption-uppercase muted mb-1">位次差分布</p>
        <p class="chart-hint muted">负值（冲刺）在左，正值（保底）在右。</p>
        <div ref="chartEl" class="hist-chart"></div>
      </DarkSurface>
    </template>
  </div>
</template>

<style scoped>
.text-muted { color: var(--c-muted); }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 14px; }
.hero { margin-bottom: 32px; }
.empty { padding: 48px 0; }

.summary { display: flex; gap: 10px; margin: 24px 0 16px; }

.sort-row { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.sort-label { font-size: 13px; margin-right: 4px; }
.sort-btn {
  padding: 6px 14px; border-radius: var(--r-control); border: 1px solid var(--c-hairline);
  background: var(--c-canvas); color: var(--c-muted); font-size: 13px; cursor: pointer;
  transition: all .15s;
}
.sort-btn:hover { color: var(--c-ink); }
.sort-btn.active { background: var(--c-surface-card); color: var(--c-ink); border-color: var(--c-surface-cream-strong); }

.school-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 48px; }
.school {
  background: var(--c-canvas); border: 1px solid var(--c-hairline);
  border-radius: var(--r-card); overflow: hidden; transition: border-color .15s;
}
.school:hover { border-color: var(--c-surface-cream-strong); }
.school-head {
  display: flex; align-items: center; gap: 16px; padding: 18px 20px; cursor: pointer;
}
.expand-icon { color: var(--c-muted); font-size: 22px; transition: transform .15s; line-height: 1; }
.expand-icon.open { transform: rotate(90deg); }
.school-main { flex: 1; display: flex; align-items: baseline; gap: 12px; min-width: 0; }
.school-name { font-family: 'Cormorant Garamond', 'Noto Serif SC', serif; font-size: 22px; color: var(--c-ink); }
.school-sub { font-size: 13px; }
.school-meta { display: flex; align-items: center; gap: 12px; }
.section-num { color: var(--c-body-strong); font-size: 16px; font-weight: 500; }

.major-list { border-top: 1px solid var(--c-hairline-soft); padding: 8px 20px 16px 48px; }
.major {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 12px 0; border-bottom: 1px solid var(--c-hairline-soft); flex-wrap: wrap;
}
.major:last-child { border-bottom: none; }
.major-name { flex: 1; color: var(--c-body); font-size: 15px; min-width: 200px; }
.major-stats { display: flex; align-items: center; gap: 16px; }
.major-stats .mono { color: var(--c-muted); }

.muted { color: var(--c-on-dark-soft); }
.chart-hint { font-size: 13px; margin-bottom: 16px; }
.hist-chart { width: 100%; height: 260px; }
</style>
