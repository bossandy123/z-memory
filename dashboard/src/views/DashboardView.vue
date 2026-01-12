<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { memoryLogAPI, type LogStats } from '../api/memory-log'
import { rlAPI, type ModelStats } from '../api/rl'

const logStats = ref<LogStats | null>(null)
const modelStats = ref<ModelStats | null>(null)
const loading = ref(false)

const statsCards = ref([
  { title: '总日志数', key: 'total_logs', color: 'bg-blue-500', value: 0 },
  { title: '已评估日志', key: 'evaluated_logs', color: 'bg-green-500', value: 0 },
  { title: '待评估日志', key: 'pending_logs', color: 'bg-yellow-500', value: 0 },
  { title: '训练样本', key: 'samples_count_last_30_days', color: 'bg-red-500', value: 0 },
])

const loadData = async () => {
  loading.value = true
  try {
    const [logStatsRes, modelStatsRes] = await Promise.all([
      memoryLogAPI.getStats(30),
      rlAPI.getModelStats(30),
    ])
    logStats.value = logStatsRes.data
    modelStats.value = modelStatsRes.data

    if (logStats.value) {
      statsCards.value[0]!.value = logStats.value.total_logs
      statsCards.value[1]!.value = logStats.value.evaluated_logs
      statsCards.value[2]!.value = logStats.value.pending_logs
    }
    if (modelStats.value) {
      statsCards.value[3]!.value = modelStats.value.samples_count_last_30_days
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    loading.value = false
  }
}

const getRewardColor = (reward: number) => {
  if (reward > 0) return 'text-green-400'
  if (reward < 0) return 'text-red-400'
  return 'text-gray-500'
}

const formatPercent = (value: number, total: number) => {
  if (total === 0) return '0%'
  return ((value / total) * 100).toFixed(1) + '%'
}

onMounted(() => loadData())
</script>

<template>
  <div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div
        v-for="card in statsCards"
        :key="card.key"
        class="p-4 flex items-center gap-4 transition-all duration-200"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }"
      >
        <div :class="['w-10 h-10 flex items-center justify-center', card.color]">
          <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="3" x2="9" y2="21"></line>
          </svg>
        </div>
        <div class="flex-1">
          <div class="text-xs font-mono mb-1" :style="{ color: 'var(--text-muted)' }">{{ card.title }}</div>
          <div class="text-2xl font-mono font-medium" :style="{ color: 'var(--text-primary)' }">{{ card.value.toLocaleString() }}</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="overflow-hidden" :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }">
        <div class="flex items-center gap-2 px-4 py-3" :style="{ borderBottom: '1px solid var(--border-color)' }">
          <svg class="w-4 h-4 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"></line>
            <line x1="12" y1="20" x2="12" y2="4"></line>
            <line x1="6" y1="20" x2="6" y2="14"></line>
          </svg>
          <h3 class="text-sm font-mono" :style="{ color: 'var(--text-primary)' }">Why-Log 统计</h3>
        </div>
        <div class="p-4" v-if="logStats">
          <div class="flex justify-between items-center py-3" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">平均奖励</span>
            <span
              class="text-sm font-mono font-medium"
              :class="getRewardColor(logStats.average_reward)"
            >
              {{ logStats.average_reward.toFixed(2) }}
            </span>
          </div>
          <div class="flex justify-between items-center py-3">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">评估率</span>
            <span class="text-sm font-mono font-medium" :style="{ color: 'var(--text-primary)' }">
              {{ formatPercent(logStats.evaluated_logs, logStats.total_logs) }}
            </span>
          </div>
        </div>
      </div>

      <div class="overflow-hidden" :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }">
        <div class="flex items-center gap-2 px-4 py-3" :style="{ borderBottom: '1px solid var(--border-color)' }">
          <svg class="w-4 h-4 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="12" x2="2" y2="12"></line>
            <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6"></path>
            <path d="M5.45 5.11L22 12"></path>
          </svg>
          <h3 class="text-sm font-mono" :style="{ color: 'var(--text-primary)' }">RL 模型统计</h3>
        </div>
        <div class="p-4" v-if="modelStats">
          <div class="flex justify-between items-center py-3" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">模型版本</span>
            <span
              class="px-2 py-1 text-xs font-mono rounded"
              :class="modelStats.model_version ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-gray-700/30 text-gray-500 border border-gray-700'"
            >
              {{ modelStats.model_version || '未加载' }}
            </span>
          </div>
          <div class="flex justify-between items-center py-3" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">检查点数量</span>
            <span class="text-sm font-mono font-medium" :style="{ color: 'var(--text-primary)' }">
              {{ modelStats.checkpoints_count }}
            </span>
          </div>
          <div class="flex justify-between items-center py-3">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">最近 30 天样本</span>
            <span class="text-sm font-mono font-medium" :style="{ color: 'var(--text-primary)' }">
              {{ modelStats.samples_count_last_30_days }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
