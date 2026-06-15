import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, type TaskConfig, type Province, type SchoolsCount } from '../api/endpoints'

export const useConfigStore = defineStore('config', () => {
  const config = ref<TaskConfig | null>(null)
  const loading = ref(false)
  const provinces = ref<Province[]>([])
  const schoolsCount = ref<SchoolsCount | null>(null)

  async function load() {
    loading.value = true
    try {
      const [cfg, prov, sc] = await Promise.all([
        api.getConfig(),
        api.getProvinces(),
        api.getSchoolsCount(),
      ])
      config.value = cfg
      provinces.value = prov
      schoolsCount.value = sc
    } finally {
      loading.value = false
    }
  }

  async function save(cfg: TaskConfig) {
    config.value = await api.putConfig(cfg)
  }

  return { config, loading, provinces, schoolsCount, load, save }
})
