import api from './index'

export interface MemoryLog {
  id: string
  memory_id: string
  memory_layer: string
  action: string
  reason: string
  metadata: any
  reward: number | null
  outcome: any
  evaluated_at: string | null
  created_at: string
}

export interface LogStats {
  total_logs: number
  evaluated_logs: number
  pending_logs: number
  average_reward: number
  action_counts: Record<string, number>
}

export const memoryLogAPI = {
  getList: (params: {
    memory_id?: string
    memory_layer?: string
    action?: string
    skip_evaluated?: boolean
    limit?: number
    offset?: number
  }) =>
    api.get<{ data: MemoryLog[]; total: number }>('/api/logs/memory', { params }),

  getDetail: (log_id: string) =>
    api.get<MemoryLog>(`/api/logs/${log_id}`),

  getStats: (days?: number) =>
    api.get<LogStats>('/api/logs/stats', { params: { days } }),

  evaluate: (log_id: string) =>
    api.post('/api/rl/reward/calculate', { log_id }),

  batchEvaluate: (params: { limit?: number; days_threshold?: number }) =>
    api.post('/api/rl/reward/evaluate', params),
}
