<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { api, type PredictResult } from '../api/endpoints'
import CCard from '../components/ui/CCard.vue'
import CInput from '../components/ui/CInput.vue'
import CButton from '../components/ui/CButton.vue'
import CBadge from '../components/ui/CBadge.vue'
import DarkSurface from '../components/ui/DarkSurface.vue'

interface Row { year: string; value: string }
const rows = ref<Row[]>([
  { year: '2021', value: '593' },
  { year: '2022', value: '591' },
  { year: '2023', value: '612' },
])
const targetYear = ref('2024')
const result = ref<PredictResult | null>(null)
const errorMsg = ref('')
const loading = ref(false)

const chartEl = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function addRow() { rows.value.push({ year: '', value: '' }) }
function removeRow(i: number) { rows.value.splice(i, 1) }

async function doPredict() {
  errorMsg.value = ''
  result.value = null
  const history: Record<string, number> = {}
  for (const r of rows.value) {
    const y = r.year.trim()
    const v = r.value.trim()
    if (!y || !v) continue
    const yn = Number(y)
    const vn = Number(v)
    if (!Number.isFinite(yn) || !Number.isFinite(vn)) {
      errorMsg.value = '年份和数值须为数字'
      return
    }
    history[String(yn)] = vn
  }
  if (Object.keys(history).length < 2) {
    errorMsg.value = '至少需要 2 个有效历史数据点'
    return
  }
  const ty = Number(targetYear.value)
  if (!Number.isFinite(ty)) {
    errorMsg.value = '请填写有效的目标年份'
    return
  }

  loading.value = true
  try {
    result.value = await api.predict(history, ty)
    await nextTick()
    updateChart()
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function updateChart() {
  if (!chart || !result.value) return
  const r = result.value
  const ty = Number(targetYear.value)
  chart.setOption({
    grid: { left: 56, right: 24, top: 24, bottom: 52 },
    tooltip: {
      trigger: 'item', backgroundColor: '#252320', borderColor: '#252320',
      textStyle: { color: '#faf9f5' },
    },
    legend: {
      data: ['历史', '拟合', '预测点'],
      textStyle: { color: '#a09d96' }, top: 0, right: 0, itemWidth: 12, itemHeight: 12,
    },
    xAxis: {
      type: 'value',
      min: Math.floor(Math.min(...r.points.map(p => p.x), ty) - 1),
      max: Math.ceil(Math.max(...r.line.map(p => p.x))),
      axisLabel: { color: '#a09d96' },
      axisLine: { lineStyle: { color: '#252320' } },
      splitLine: { lineStyle: { color: '#1f1e1b' } },
      name: '年份', nameTextStyle: { color: '#a09d96' }, nameLocation: 'middle', nameGap: 32,
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#a09d96' },
      splitLine: { lineStyle: { color: '#1f1e1b' } },
      name: '分数 / 位次', nameTextStyle: { color: '#a09d96' }, nameLocation: 'middle', nameGap: 44,
    },
    series: [
      {
        name: '历史', type: 'scatter', symbolSize: 12,
        data: r.points.map(p => [p.x, p.y]),
        itemStyle: { color: '#cc785c' },
      },
      {
        name: '拟合', type: 'line', data: r.line.map(p => [p.x, p.y]),
        showSymbol: false, lineStyle: { color: '#8e8b82', width: 2, type: 'dashed' },
      },
      {
        name: '预测点', type: 'scatter', symbolSize: 16,
        data: [[ty, r.predicted]],
        itemStyle: { color: '#e8a55a', borderColor: '#fff', borderWidth: 2 },
        markLine: {
          symbol: 'none', silent: true, label: { show: false },
          data: [{ xAxis: ty, lineStyle: { color: '#e8a55a', type: 'dashed', width: 1 } }],
        },
      },
    ],
  }, true)
}

function onResize() { chart?.resize() }

onMounted(async () => {
  await nextTick()
  if (chartEl.value) {
    chart = echarts.init(chartEl.value)
    chart.setOption({
      grid: { left: 56, right: 24, top: 24, bottom: 52 },
      xAxis: { type: 'value', axisLabel: { color: '#a09d96' }, axisLine: { lineStyle: { color: '#252320' } }, splitLine: { lineStyle: { color: '#1f1e1b' } } },
      yAxis: { type: 'value', axisLabel: { color: '#a09d96' }, splitLine: { lineStyle: { color: '#1f1e1b' } } },
    })
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
      <p class="t-caption-uppercase text-muted mb-3">分数预测</p>
      <h1 style="font-size: 40px;">一元线性回归预测</h1>
      <p class="text-muted mt-2">录入历史年份的分数或位次，预测下一年的趋势。数据点越多、相关性越高，预测越可信。</p>
    </section>

    <div class="grid">
      <!-- 录入表单 -->
      <CCard variant="cream">
        <h2 class="section-title">历史数据</h2>
        <div class="rows">
          <div class="row-head">
            <span class="text-muted row-label">年份</span>
            <span class="text-muted row-label">分数 / 位次</span>
            <span></span>
          </div>
          <div v-for="(r, i) in rows" :key="i" class="row">
            <input class="cell" type="number" v-model="r.year" placeholder="2021" />
            <input class="cell" type="number" v-model="r.value" placeholder="593" />
            <button class="del" :disabled="rows.length <= 1" @click="removeRow(i)">×</button>
          </div>
        </div>
        <button class="add-btn" @click="addRow">+ 添加年份</button>

        <div class="target-row">
          <CInput v-model="targetYear" label="目标年份" type="number" />
        </div>

        <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
        <div class="cta">
          <CButton variant="primary" :disabled="loading" @click="doPredict">
            {{ loading ? '计算中…' : '预测' }}
          </CButton>
        </div>
      </CCard>

      <!-- 图表 + 方程 -->
      <div class="result-col">
        <DarkSurface>
          <p class="t-caption-uppercase muted mb-2">回归图</p>
          <div ref="chartEl" class="chart"></div>
        </DarkSurface>

        <div v-if="result" class="equations">
          <div class="pred-line">
            <CBadge variant="coral">预测 {{ targetYear }} ≈ {{ Math.round(result.predicted) }}</CBadge>
          </div>
          <div class="eq-row mono">{{ result.equation_str }}</div>
          <div class="eq-grid">
            <div class="eq-cell"><span class="muted">相关系数 r</span><span class="mono big">{{ result.r.toFixed(3) }}</span></div>
            <div class="eq-cell"><span class="muted">决定系数 R²</span><span class="mono big">{{ result.r_squared.toFixed(3) }}</span></div>
          </div>
        </div>
        <div v-else class="placeholder text-muted">填写历史数据后点击「预测」查看结果。</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.text-muted { color: var(--c-muted); }
.mono { font-family: 'JetBrains Mono', monospace; }
.muted { color: var(--c-muted); }
.hero { margin-bottom: 32px; }

.grid { display: grid; grid-template-columns: 1fr; gap: 32px; align-items: start; }
@media (min-width: 960px) { .grid { grid-template-columns: 1fr 1.1fr; } }

.section-title { font-size: 22px; margin-bottom: 20px; }

.rows { display: flex; flex-direction: column; gap: 10px; }
.row-head, .row { display: grid; grid-template-columns: 1fr 1fr 32px; gap: 12px; align-items: center; }
.row-label { font-size: 12px; }
.cell {
  height: 40px; padding: 0 12px; border: 1px solid var(--c-hairline); border-radius: var(--r-control);
  background: var(--c-canvas); color: var(--c-ink); font-size: 15px; font-family: inherit; outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.cell:focus { border-color: var(--c-primary); box-shadow: 0 0 0 3px rgba(204, 120, 92, 0.15); }
.del {
  width: 32px; height: 32px; border-radius: var(--r-control); border: 1px solid var(--c-hairline);
  background: var(--c-canvas); color: var(--c-muted); font-size: 18px; cursor: pointer;
}
.del:hover:not(:disabled) { color: var(--c-error); border-color: var(--c-error); }
.del:disabled { opacity: .4; cursor: not-allowed; }

.add-btn {
  margin-top: 14px; background: transparent; border: none; color: var(--c-primary);
  font-size: 14px; font-weight: 500; cursor: pointer; padding: 6px 0;
}
.add-btn:hover { text-decoration: underline; }

.target-row { margin-top: 20px; max-width: 220px; }
.error { color: var(--c-error); font-size: 14px; margin-top: 16px; }
.cta { margin-top: 20px; }

.result-col { display: flex; flex-direction: column; gap: 20px; }
.chart { width: 100%; height: 320px; }

.equations {
  background: var(--c-surface-card); border-radius: var(--r-card); padding: 24px;
}
.pred-line { margin-bottom: 16px; }
.eq-row { font-size: 16px; color: var(--c-ink); padding: 12px 16px; background: var(--c-canvas); border-radius: var(--r-control); margin-bottom: 16px; }
.eq-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.eq-cell { display: flex; flex-direction: column; gap: 4px; }
.big { font-size: 20px; color: var(--c-ink); }

.placeholder { padding: 24px; font-size: 15px; }
</style>
