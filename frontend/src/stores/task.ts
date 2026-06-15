import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type Progress, type TaskConfig } from '../api/endpoints'

const ACTIVE_STATES = new Set(['running', 'pending', 'pausing', 'cancelling'])

export const useTaskStore = defineStore('task', () => {
  const current = ref<Progress | null>(null)
  const taskId = ref<string | null>(null)
  let timer: ReturnType<typeof setInterval> | null = null

  const isRunning = computed(() => ACTIVE_STATES.has(current.value?.status || ''))
  const isDone = computed(() => current.value?.status === 'done')
  const isPaused = computed(() => current.value?.status === 'paused')
  const pct = computed(() => {
    const c = current.value
    if (!c || !c.total) return 0
    return Math.round((c.processed / c.total) * 100)
  })

  async function start(cfg: TaskConfig) {
    const res = await api.startTask(cfg)
    taskId.value = res.task_id
    await poll()
    startPolling()
    return res
  }

  async function resume(taskIdStr: string) {
    taskId.value = taskIdStr
    await poll()
    startPolling()
  }

  async function poll() {
    if (!taskId.value) return
    try {
      current.value = await api.getProgress(taskId.value)
    } catch {
      current.value = null
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
  }

  return { current, taskId, isRunning, isDone, isPaused, pct, start, resume, poll, startPolling, stopPolling, pause, cancel, reset }
})
