import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type Progress, type TaskConfig } from '../api/endpoints'
import { ApiError } from '../api/client'

const ACTIVE_STATES = new Set(['running', 'pending', 'pausing', 'cancelling'])
const TERMINAL_STATES = new Set(['done', 'cancelled', 'error'])
const TASK_ID_KEY = 'score_to_school:task_id'

function loadTaskIdFromStorage(): string | null {
  try {
    return localStorage.getItem(TASK_ID_KEY)
  } catch {
    return null
  }
}

function saveTaskIdToStorage(id: string | null) {
  try {
    if (id) localStorage.setItem(TASK_ID_KEY, id)
    else localStorage.removeItem(TASK_ID_KEY)
  } catch {
    /* localStorage 不可用（隐私模式等），忽略 */
  }
}

export const useTaskStore = defineStore('task', () => {
  const current = ref<Progress | null>(null)
  const taskId = ref<string | null>(null)
  const resuming = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  const isRunning = computed(() => ACTIVE_STATES.has(current.value?.status || ''))
  const isDone = computed(() => current.value?.status === 'done')
  const isPaused = computed(() => current.value?.status === 'paused')
  const isInterrupted = computed(() => current.value?.status === 'interrupted')
  const pct = computed(() => {
    const c = current.value
    if (!c || !c.total) return 0
    return Math.round((c.processed / c.total) * 100)
  })

  async function start(cfg: TaskConfig) {
    const res = await api.startTask(cfg)
    taskId.value = res.task_id
    saveTaskIdToStorage(res.task_id)
    await poll()
    startPolling()
    return res
  }

  // 接管一个已知 task_id（不重新发起任务，仅恢复轮询）。用于刷新/历史页恢复。
  async function resume(taskIdStr: string) {
    taskId.value = taskIdStr
    saveTaskIdToStorage(taskIdStr)
    await poll()
    if (current.value && ACTIVE_STATES.has(current.value.status)) startPolling()
  }

  async function poll() {
    if (!taskId.value) return
    try {
      current.value = await api.getProgress(taskId.value)
      // 进入终态：停止轮询并清掉本地 task_id（避免下次刷新还接管已结束的任务）
      if (current.value && TERMINAL_STATES.has(current.value.status)) {
        stopPolling()
        saveTaskIdToStorage(null)
      }
    } catch (e) {
      // 404：任务已被清盘或进程重启无此 task —— 用列表兜底，找不到就优雅回 idle
      if (e instanceof ApiError && e.status === 404) {
        await refreshFromList()
      } else {
        current.value = null
      }
    }
  }

  // 用 /api/task 列表重新校准当前任务状态（poll 404、或刷新后校验用）。
  // 找不到对应 task 则视为彻底消失，清空回 idle。
  async function refreshFromList() {
    if (!taskId.value) {
      current.value = null
      return
    }
    try {
      const list = await api.listTasks()
      const match = list.find((t) => t.task_id === taskId.value)
      if (match) {
        current.value = match
        if (ACTIVE_STATES.has(match.status)) startPolling()
        else stopPolling()
      } else {
        // 任务确实没了（cancel 清盘 / 历史已清）
        current.value = null
        taskId.value = null
        saveTaskIdToStorage(null)
        stopPolling()
      }
    } catch {
      current.value = null
    }
  }

  // 应用启动时（App.vue onMounted）调用：从 localStorage 取 task_id，
  // 用列表校验后接管。返回是否成功接管到运行中任务。
  // 关键：只接管"轮询"，绝不自动重新 start —— interrupted/paused 由用户点按钮恢复。
  async function autoTakeover(): Promise<boolean> {
    const id = loadTaskIdFromStorage()
    if (!id) return false
    resuming.value = true
    try {
      const list = await api.listTasks()
      const match = list.find((t) => t.task_id === id)
      if (!match) {
        // localStorage 里的 task_id 已过期/被清
        saveTaskIdToStorage(null)
        return false
      }
      taskId.value = id
      current.value = match
      if (ACTIVE_STATES.has(match.status)) {
        startPolling()
      }
      return true
    } catch {
      return false
    } finally {
      resuming.value = false
    }
  }

  function startPolling() {
    stopPolling()
    timer = setInterval(async () => {
      await poll()
      if (current.value && !ACTIVE_STATES.has(current.value.status)) stopPolling()
    }, 2000)
  }

  function stopPolling() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  async function pause() {
    if (taskId.value) await api.pauseTask(taskId.value)
  }
  async function cancel() {
    if (taskId.value) await api.cancelTask(taskId.value)
  }
  function reset() {
    stopPolling()
    current.value = null
    taskId.value = null
    saveTaskIdToStorage(null)
  }

  return {
    current, taskId, resuming,
    isRunning, isDone, isPaused, isInterrupted, pct,
    start, resume, poll, refreshFromList, autoTakeover,
    startPolling, stopPolling, pause, cancel, reset,
  }
})
