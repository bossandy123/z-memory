import api from './index'

export interface TrainingSample {
  id: string
  log_id: string
  entity_id: string
  entity_type: string
  state: any
  action: string
  reward: number
  next_state: any
  done: boolean
  created_at: string
}

export interface ModelCheckpoint {
  id: string
  model_name: string
  version: string
  model_data: any
  metrics: any
  created_at: string
}

export interface ModelStats {
  model_name: string
  model_version: string | null
  samples_count_last_30_days: number
  average_reward: number
  checkpoints_count: number
  current_weights: any
}

export const rlAPI = {
  getSamples: (params: {
    entity_id?: string
    entity_type?: string
    min_reward?: number
    max_reward?: number
    limit?: number
    offset?: number
  }) =>
    api.get<{ data: TrainingSample[]; total: number }>('/api/rl/training/samples', { params }),

  getCheckpoints: (params?: {
    model_name?: string
    version?: string
    limit?: number
  }) =>
    api.get<{ data: ModelCheckpoint[]; total: number }>('/api/rl/model/checkpoints', { params }),

  getModelStats: (days?: number) =>
    api.get<ModelStats>('/api/rl/model/statistics', { params: { days } }),

  downloadCheckpoint: (checkpoint_id: string) =>
    api.get<{ data: any }>(`/api/rl/model/checkpoint/${checkpoint_id}/download`),

  saveCheckpoint: (metrics?: any) =>
    api.post('/api/rl/model/save', { metrics }),

  loadLatestModel: () =>
    api.post<{ data: any }>('/api/rl/model/load'),

  train: (params: { days?: number; epochs?: number; save_checkpoint?: boolean }) =>
    api.post('/api/rl/train', params),

  getHealth: () =>
    api.get('/api/rl/health'),
}
