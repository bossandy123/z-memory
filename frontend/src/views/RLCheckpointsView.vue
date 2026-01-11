<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { rlAPI, type ModelCheckpoint } from '../api/rl'

const checkpoints = ref<ModelCheckpoint[]>([])
const loading = ref(false)
const total = ref(0)

const filterForm = ref({
  model_name: '',
  version: '',
})

const pageSize = ref(20)

const trainDialogVisible = ref(false)
const trainForm = ref({
  days: 30,
  epochs: 10,
  save_checkpoint: true,
})

const loadCheckpoints = async () => {
  loading.value = true
  try {
    const res = await rlAPI.getCheckpoints({
      ...filterForm.value,
      limit: pageSize.value,
    })
    checkpoints.value = res.data.data
    total.value = res.data.total
  } catch (error) {
    console.error('Failed to load checkpoints:', error)
  } finally {
    loading.value = false
  }
}

const handleDownload = async (checkpoint: ModelCheckpoint) => {
  try {
    const data = {
      id: checkpoint.id,
      model_name: checkpoint.model_name,
      version: checkpoint.version,
      model_data: checkpoint.model_data,
      metrics: checkpoint.metrics,
      created_at: checkpoint.created_at,
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${checkpoint.model_name}-${checkpoint.version}.json`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download:', error)
  }
}

const handleTrain = async () => {
  try {
    await rlAPI.train({
      days: trainForm.value.days,
      epochs: trainForm.value.epochs,
      save_checkpoint: trainForm.value.save_checkpoint,
    })
    trainDialogVisible.value = false
    loadCheckpoints()
  } catch (error) {
    console.error('Failed to train:', error)
  }
}

const handleSaveCheckpoint = async () => {
  try {
    await rlAPI.saveCheckpoint()
    loadCheckpoints()
  } catch (error) {
    console.error('Failed to save checkpoint:', error)
  }
}

const hasMetrics = (metrics: any) => {
  return metrics && Object.keys(metrics).length > 0
}

onMounted(() => loadCheckpoints())
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-4 flex-wrap">
      <input
        v-model="filterForm.model_name"
        placeholder="模型名称"
        class="px-3 py-1.5 w-40 bg-gray-800 border border-gray-700 text-sm text-gray-300 font-mono placeholder-gray-600 focus:outline-none focus:border-blue-500/50"
      />

      <input
        v-model="filterForm.version"
        placeholder="版本"
        class="px-3 py-1.5 w-32 bg-gray-800 border border-gray-700 text-sm text-gray-300 font-mono placeholder-gray-600 focus:outline-none focus:border-blue-500/50"
      />

      <button
        @click="loadCheckpoints"
        class="px-3 py-1.5 border border-gray-700 bg-gray-800 text-gray-400 text-xs font-mono hover:bg-gray-700 hover:text-gray-300 transition-colors"
      >
        刷新
      </button>

      <button
        @click="handleSaveCheckpoint"
        class="px-3 py-1.5 border border-gray-700 bg-gray-800 text-gray-400 text-xs font-mono hover:bg-gray-700 hover:text-gray-300 transition-colors"
      >
        保存检查点
      </button>

      <button
        @click="trainDialogVisible = true"
        class="px-3 py-1.5 bg-green-500 text-white text-xs font-mono hover:bg-green-600 transition-colors"
      >
        开始训练
      </button>
    </div>

    <div class="mb-4">
      <div class="bg-gray-800 border border-gray-700 overflow-hidden">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-gray-850">
              <th class="px-3 py-2 text-left text-xs font-mono text-gray-500 border-b border-gray-700">检查点 ID</th>
              <th class="px-3 py-2 text-left text-xs font-mono text-gray-500 border-b border-gray-700">模型名称</th>
              <th class="px-3 py-2 text-left text-xs font-mono text-gray-500 border-b border-gray-700">版本</th>
              <th class="px-3 py-2 text-left text-xs font-mono text-gray-500 border-b border-gray-700">指标</th>
              <th class="px-3 py-2 text-left text-xs font-mono text-gray-500 border-b border-gray-700">创建时间</th>
              <th class="px-3 py-2 text-left text-xs font-mono text-gray-500 border-b border-gray-700">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="checkpoint in checkpoints"
              :key="checkpoint.id"
              class="transition-colors hover:bg-gray-700/50"
            >
              <td class="px-3 py-2 text-xs text-gray-500 font-mono">{{ checkpoint.id.slice(0, 16) }}...</td>
              <td class="px-3 py-2 text-sm text-gray-300 font-mono">{{ checkpoint.model_name }}</td>
              <td class="px-3 py-2 text-sm text-gray-300 font-mono">{{ checkpoint.version }}</td>
              <td class="px-3 py-2 text-sm text-gray-300 font-mono">
                <span v-if="hasMetrics(checkpoint.metrics)">
                  {{ Object.keys(checkpoint.metrics).length }} 个指标
                </span>
                <span v-else class="text-gray-600">无</span>
              </td>
              <td class="px-3 py-2 text-xs text-gray-500 font-mono">
                {{ new Date(checkpoint.created_at).toLocaleString() }}
              </td>
              <td class="px-3 py-2">
                <button
                  @click="handleDownload(checkpoint)"
                  class="text-blue-400 hover:text-blue-300 text-xs font-mono"
                >
                  下载
                </button>
              </td>
            </tr>
            <tr v-if="checkpoints.length === 0">
              <td colspan="6" class="px-3 py-8 text-center text-gray-600 text-xs font-mono">
                暂无数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="flex justify-center">
      <select
        v-model="pageSize"
        @change="loadCheckpoints"
        class="px-2 py-1 bg-gray-800 border border-gray-700 text-xs text-gray-400 font-mono focus:outline-none focus:border-blue-500/50"
      >
        <option :value="10">10/页</option>
        <option :value="20">20/页</option>
        <option :value="50">50/页</option>
      </select>
    </div>

    <div v-if="trainDialogVisible" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm">
      <div class="bg-gray-800 border border-gray-700 max-w-sm w-full mx-4 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-700">
          <h3 class="text-sm font-mono text-gray-300">开始训练</h3>
        </div>
        <div class="p-4 space-y-3">
          <div>
            <label class="block text-xs text-gray-500 font-mono mb-1">数据天数</label>
            <input
              v-model="trainForm.days"
              type="number"
              :min="1"
              :max="365"
              class="w-full px-3 py-1.5 bg-gray-900 border border-gray-700 text-sm text-gray-300 font-mono focus:outline-none focus:border-blue-500/50"
            >
          </div>
          <div>
            <label class="block text-xs text-gray-500 font-mono mb-1">训练轮数</label>
            <input
              v-model="trainForm.epochs"
              type="number"
              :min="1"
              :max="100"
              class="w-full px-3 py-1.5 bg-gray-900 border border-gray-700 text-sm text-gray-300 font-mono focus:outline-none focus:border-blue-500/50"
            >
          </div>
          <div class="flex items-center gap-2">
            <label class="text-xs text-gray-500 font-mono">保存检查点</label>
            <input
              v-model="trainForm.save_checkpoint"
              type="checkbox"
              class="w-4 h-4 rounded border-gray-700 bg-gray-900 text-blue-500 focus:ring-2 focus:ring-blue-500/50"
            >
          </div>
        </div>
        <div class="px-4 py-3 border-t border-gray-700 flex justify-end gap-2">
          <button
            @click="trainDialogVisible = false"
            class="px-3 py-1.5 border border-gray-700 bg-gray-900 text-gray-400 text-xs font-mono hover:bg-gray-800 hover:text-gray-300 transition-colors"
          >
            取消
          </button>
          <button
            @click="handleTrain"
            class="px-3 py-1.5 bg-green-500 text-white text-xs font-mono hover:bg-green-600 transition-colors"
          >
            开始
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
