<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { memoryLogAPI, type MemoryLog } from '../api/memory-log'

const logs = ref<MemoryLog[]>([])
const loading = ref(false)
const total = ref(0)

const filterForm = ref({
  memory_id: '',
  memory_layer: '',
  action: '',
  skip_evaluated: false,
})

const currentPage = ref(1)
const pageSize = ref(20)

const detailVisible = ref(false)
const selectedLog = ref<MemoryLog | null>(null)

const loadLogs = async () => {
  loading.value = true
  try {
    const res = await memoryLogAPI.getList({
      ...filterForm.value,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
    })
    logs.value = res.data.data
    total.value = res.data.total
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadLogs()
}

const showDetail = (log: MemoryLog) => {
  selectedLog.value = log
  detailVisible.value = true
}

const handleEvaluate = async (logId: string) => {
  try {
    await memoryLogAPI.evaluate(logId)
    loadLogs()
  } catch (error) {
    console.error('Failed to evaluate:', error)
  }
}

const handleExport = () => {
  const data = logs.value.map(log => JSON.stringify(log, null, 2)).join('\n')
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `why-logs-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  URL.revokeObjectURL(url)
}

const getActionTagType = (action: string) => {
  const types: Record<string, { color: string }> = {
    insert: { color: 'bg-green-500/10 text-green-400 border border-green-500/20' },
    update: { color: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' },
    delete: { color: 'bg-red-500/10 text-red-400 border border-red-500/20' },
    ignore: { color: 'bg-gray-700/30 text-gray-500 border border-gray-700' },
  }
  return types[action] || { color: 'bg-gray-700/30 text-gray-500 border border-gray-700' }
}

const getActionText = (action: string) => {
  const text: Record<string, string> = {
    insert: '插入',
    update: '更新',
    delete: '删除',
    ignore: '忽略',
  }
  return text[action] || action
}

const getLayerText = (layer: string) => {
  const text: Record<string, string> = {
    profile: 'Profile',
    event: 'Event',
  }
  return text[layer] || layer
}

const getLayerColor = (layer: string) => {
  const colors: Record<string, string> = {
    profile: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20',
    event: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
  }
  return colors[layer] || 'bg-gray-700/30 text-gray-500 border border-gray-700'
}

onMounted(() => loadLogs())
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-4 flex-wrap">
      <div class="relative">
        <input
          v-model="filterForm.memory_id"
          placeholder="记忆 ID"
          class="pl-8 pr-3 py-1.5 w-40 text-sm font-mono focus:outline-none focus:border-blue-500/50"
          :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
        >
      </div>

      <select
        v-model="filterForm.memory_layer"
        class="px-3 py-1.5 w-32 text-sm font-mono focus:outline-none focus:border-blue-500/50"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
      >
        <option value="">层级</option>
        <option value="profile">Profile</option>
        <option value="event">Event</option>
      </select>

      <select
        v-model="filterForm.action"
        class="px-3 py-1.5 w-28 text-sm font-mono focus:outline-none focus:border-blue-500/50"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
      >
        <option value="">操作</option>
        <option value="insert">插入</option>
        <option value="update">更新</option>
        <option value="delete">删除</option>
        <option value="ignore">忽略</option>
      </select>

      <label class="flex items-center gap-2 text-xs font-mono" :style="{ color: 'var(--text-secondary)' }">
        <input v-model="filterForm.skip_evaluated" type="checkbox" class="w-3.5 h-3.5 rounded text-blue-500 focus:ring-2 focus:ring-blue-500/50">
        未评估
      </label>

      <button
        @click="handleSearch"
        class="px-3 py-1.5 bg-blue-500 text-white text-xs font-mono hover:bg-blue-600 transition-colors"
      >
        搜索
      </button>

      <button
        @click="loadLogs"
        class="px-3 py-1.5 border text-xs font-mono transition-colors"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
      >
        刷新
      </button>

      <button
        @click="handleExport"
        class="px-3 py-1.5 border text-xs font-mono transition-colors"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
      >
        导出
      </button>
    </div>

    <div class="mb-4">
      <div class="overflow-hidden" :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }">
        <table class="w-full border-collapse">
          <thead>
            <tr :style="{ backgroundColor: 'var(--bg-tertiary)' }">
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">日志 ID</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">层级</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">操作</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">原因</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">奖励</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">创建时间</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="log in logs"
              :key="log.id"
              @click="showDetail(log)"
              class="cursor-pointer transition-colors"
              :style="{ backgroundColor: 'transparent' }"
              @mouseover="(e) => e.currentTarget.style.backgroundColor = 'var(--hover-bg)'"
              @mouseout="(e) => e.currentTarget.style.backgroundColor = 'transparent'"
            >
              <td class="px-3 py-2 text-xs font-mono" :style="{ color: 'var(--text-muted)' }">{{ log.id.slice(0, 8) }}...</td>
              <td class="px-3 py-2">
                <span :class="['px-2 py-0.5 text-xs font-mono rounded', getLayerColor(log.memory_layer)]">
                  {{ getLayerText(log.memory_layer) }}
                </span>
              </td>
              <td class="px-3 py-2">
                <span :class="['px-2 py-0.5 text-xs font-mono rounded', getActionTagType(log.action).color]">
                  {{ getActionText(log.action) }}
                </span>
              </td>
              <td class="px-3 py-2 text-sm font-mono max-w-xs truncate" :style="{ color: 'var(--text-secondary)' }">
                {{ log.reason.slice(0, 40) }}{{ log.reason.length > 40 ? '...' : '' }}
              </td>
              <td class="px-3 py-2">
                <span
                  v-if="log.reward !== null"
                  class="text-sm font-mono font-medium"
                  :class="{
                    'text-green-400': log.reward > 0,
                    'text-red-400': log.reward < 0,
                  }"
                >
                  {{ log.reward.toFixed(2) }}
                </span>
                <span v-else class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">-</span>
              </td>
              <td class="px-3 py-2 text-xs font-mono" :style="{ color: 'var(--text-muted)' }">
                {{ new Date(log.created_at).toLocaleString() }}
              </td>
              <td class="px-3 py-2">
                <button
                  @click.stop="showDetail(log)"
                  class="text-blue-400 hover:text-blue-300 text-xs font-mono"
                >
                  详情
                </button>
                <button
                  v-if="log.reward === null"
                  @click.stop="handleEvaluate(log.id)"
                  class="text-yellow-400 hover:text-yellow-300 text-xs font-mono ml-2"
                >
                  评估
                </button>
              </td>
            </tr>
            <tr v-if="logs.length === 0">
              <td colspan="7" class="px-3 py-8 text-center text-xs font-mono" :style="{ color: 'var(--text-muted)' }">
                暂无数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="flex justify-center">
      <div class="flex items-center gap-2">
        <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">{{ total }} 条记录</span>
        <select
          v-model="pageSize"
          @change="loadLogs"
          class="px-2 py-1 text-xs font-mono focus:outline-none focus:border-blue-500/50"
          :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
        >
          <option :value="10">10/页</option>
          <option :value="20">20/页</option>
          <option :value="50">50/页</option>
          <option :value="100">100/页</option>
        </select>
      </div>
    </div>

    <div v-if="detailVisible && selectedLog" class="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm" :style="{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }">
      <div class="max-w-md w-full mx-4 overflow-hidden" :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }">
        <div class="flex items-center justify-between px-4 py-3" :style="{ borderBottom: '1px solid var(--border-color)' }">
          <h3 class="text-sm font-mono" :style="{ color: 'var(--text-primary)' }">日志详情</h3>
          <button @click="detailVisible = false" :style="{ color: 'var(--text-muted)' }">
            <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="p-4 space-y-3">
          <div class="flex justify-between items-center py-2" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">日志 ID</span>
            <span class="text-xs font-mono" :style="{ color: 'var(--text-primary)' }">{{ selectedLog.id }}</span>
          </div>
          <div class="flex justify-between items-center py-2" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">记忆 ID</span>
            <span class="text-xs font-mono" :style="{ color: 'var(--text-primary)' }">{{ selectedLog.memory_id }}</span>
          </div>
          <div class="flex justify-between items-center py-2" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">层级</span>
            <span :class="['px-2 py-0.5 text-xs font-mono rounded', getLayerColor(selectedLog.memory_layer)]">
              {{ getLayerText(selectedLog.memory_layer) }}
            </span>
          </div>
          <div class="flex justify-between items-center py-2" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">操作</span>
            <span :class="['px-2 py-0.5 text-xs font-mono rounded', getActionTagType(selectedLog.action).color]">
              {{ getActionText(selectedLog.action) }}
            </span>
          </div>
          <div class="py-2" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono block mb-1" :style="{ color: 'var(--text-muted)' }">原因</span>
            <span class="text-xs font-mono" :style="{ color: 'var(--text-primary)' }">{{ selectedLog.reason }}</span>
          </div>
          <div class="flex justify-between items-center py-2" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">奖励</span>
            <span
              v-if="selectedLog.reward !== null"
              class="text-xs font-mono font-medium"
              :class="{
                'text-green-400': selectedLog.reward > 0,
                'text-red-400': selectedLog.reward < 0,
              }"
            >
              {{ selectedLog.reward.toFixed(2) }}
            </span>
            <span v-else class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">未评估</span>
          </div>
          <div class="flex justify-between items-center py-2" :style="{ borderBottom: '1px solid var(--border-color)' }">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">创建时间</span>
            <span class="text-xs font-mono" :style="{ color: 'var(--text-primary)' }">{{ new Date(selectedLog.created_at).toLocaleString() }}</span>
          </div>
          <div class="flex justify-between items-center py-2">
            <span class="text-xs font-mono" :style="{ color: 'var(--text-muted)' }">评估时间</span>
            <span class="text-xs font-mono" :style="{ color: 'var(--text-primary)' }">
              {{ selectedLog.evaluated_at ? new Date(selectedLog.evaluated_at).toLocaleString() : '-' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
