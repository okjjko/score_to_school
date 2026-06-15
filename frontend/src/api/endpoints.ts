import { http } from './client'

export interface TaskConfig {
  province_id: number
  rank: number
  want: string
  year: number
  ethnic_minority: boolean
  output: string
  subject: string[]
  thread_num: number
}

export interface Province { id: number; name: string }
export interface SchoolsCount { total: number; usable: number }

export interface Progress {
  task_id: string
  status: string
  phase: string | null
  processed: number
  total: number
  matched: number
  school: string | null
  remaining_sec: number | null
  message: string | null
  error: string | null
  last_update?: number
}

export interface ResultFile { file: string; want: string; year: string; size_kb: number; mtime: number }

export interface ResumeItem {
  task_id: string
  province_id: string
  want: string
  year: number
  rank: number
  processed_count: number
  results_count: number
}

export interface PredictResult {
  slope: number
  intercept: number
  r: number
  r_squared: number
  predicted: number
  equation_str: string
  points: { x: number; y: number }[]
  line: { x: number; y: number }[]
}

/** 结果项：[{ 学校名: [{ 专业名: { min, min_section } }] }] */
export type SchoolResult = Record<string, { min: string | number; min_section: string | number }>[]

export const api = {
  getConfig: () => http.get<TaskConfig>('/config'),
  putConfig: (cfg: TaskConfig) => http.put<TaskConfig>('/config', cfg),
  getProvinces: () => http.get<Province[]>('/meta/provinces'),
  getSchoolsCount: () => http.get<SchoolsCount>('/meta/schools-count'),
  startTask: (cfg: TaskConfig) => http.post<{ task_id: string; status: string }>('/task/start', cfg),
  getProgress: (id: string) => http.get<Progress>(`/task/${id}/progress`),
  pauseTask: (id: string) => http.post<{ ok: boolean }>(`/task/${id}/pause`),
  cancelTask: (id: string) => http.post<{ ok: boolean }>(`/task/${id}/cancel`),
  getResult: (id: string) => http.get<SchoolResult>(`/task/${id}/result`),
  listResume: () => http.get<ResumeItem[]>('/resume'),
  getResume: (id: string) => http.get<ResumeItem>(`/resume/${id}`),
  deleteResume: (id: string) => http.del<{ ok: boolean }>(`/resume/${id}`),
  listResults: () => http.get<ResultFile[]>('/results'),
  readResult: (file: string) => http.get<SchoolResult>(`/results/${encodeURIComponent(file)}`),
  predict: (history: Record<string, number>, target_year: number) =>
    http.post<PredictResult>('/predict', { history, target_year }),
}
