<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { rlAPI, type TrainingSample } from '../api/rl'

const samples = ref<TrainingSample[]>([])
const loading = ref(false)
const total = ref(0)

const filterForm = ref({
  entity_id: '',
  entity_type: '',
  min_reward: undefined as number | undefined,
  max_reward: undefined as number | undefined,
})

const currentPage = ref(1)
const pageSize = ref(20)

const loadSamples = async () => {
  loading.value = true
  try {
    const res = await rlAPI.getSamples({
      ...filterForm.value,
      limit: pageSize.value,
      offset: (currentPage.value -1) * pageSize.value,
    })
    samples.value = res.data.data
    total.value = res.data.total
  } catch (error) {
    console.error('Failed to load samples:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadSamples()
}

const getRewardClass = (reward: number) => {
  if (reward > 0.5) return 'text-green-400 bg-green-500/10 border border-green-500/20'
  if (reward < -0.5) return 'text-red-400 bg-red-500/10 border border-red-500/20'
  return 'text-gray-500 bg-gray-700/30 border border-gray-700'
}

const getEntityTypeText = (type: string) => {
  const text: Record<string, string> = {
    user: '用户',
    agent: '代理',
  }
  return text[type] || type
}

onMounted(() => loadSamples())
</script>

<template>
  <div>
    <div class="flex items-center gap-2 px-0 py-3 mb-4 flex-wrap">
      <input
        v-model="filterForm.entity_id"
        placeholder="实体 ID"
        class="px-3 py-1.5 w-40 text-sm font-mono focus:outline-none focus:border-blue-500/50"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
      />

      <select
        v-model="filterForm.entity_type"
        class="px-3 py-1.5 w-32 text-sm font-mono focus:outline-none focus:border-blue-500/50"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
      >
        <option value="">类型</option>
        <option value="user">User</option>
        <option value="agent">Agent</option>
      </select>

      <input
        v-model="filterForm.min_reward"
        type="number"
        placeholder="最小奖励"
        class="px-3 py-1.5 w-28 text-sm font-mono focus:outline-none focus:border-blue-500/50"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
      />

      <input
        v-model="filterForm.max_reward"
        type="number"
        placeholder="最大奖励"
        class="px-3 py-1.5 w-28 text-sm font-mono focus:outline-none focus:border-blue-500/50"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
      />

      <button
        @click="handleSearch"
        class="px-3 py-1.5 bg-blue-500 text-white text-xs font-mono hover:bg-blue-600 transition-colors"
      >
        搜索
      </button>

      <button
        @click="loadSamples"
        class="px-3 py-1.5 border text-xs font-mono transition-colors"
        :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
      >
        刷新
      </button>
    </div>

    <div class="mb-4">
      <div class="overflow-hidden" :style="{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }">
        <table class="w-full border-collapse">
          <thead>
            <tr :style="{ backgroundColor: 'var(--bg-tertiary)' }">
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">样本 ID</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">类型</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">实体 ID</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">操作</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">奖励</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">完成</th>
              <th class="px-3 py-2 text-left text-xs font-mono border-b" :style="{ color: 'var(--text-muted)', borderColor: 'var(--border-color)' }">创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sample in samples"
              :key="sample.id"
              class="transition-colors"
              :style="{ backgroundColor: 'transparent' }"
              @mouseover="(e) => e.currentTarget.style.backgroundColor = 'var(--hover-bg)'"
              @mouseout="(e) => e.currentTarget.style.backgroundColor = 'transparent'"
            >
              <td class="px-3 py-2 text-xs font-mono" :style="{ color: 'var(--text-muted)' }">{{ sample.id.slice(0, 12) }}...</td>
              <td class="px-3 py-2">
                <span class="px-2 py-0.5 text-xs font-mono rounded" :class="sample.entity_type === 'user' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'">
                  {{ getEntityTypeText(sample.entity_type) }}
                </span>
              </td>
              <td class="px-3 py-2 text-sm font-mono" :style="{ color: 'var(--text-primary)' }">{{ sample.entity_id }}</td>
              <td class="px-3 py-2 text-sm font-mono" :style="{ color: 'var(--text-primary)' }">{{ sample.action }}</td>
              <td class="px-3 py-2">
                <span :class="['px-2 py-0.5 text-xs font-mono rounded', getRewardClass(sample.reward)]">
                  {{ sample.reward.toFixed(2) }}
                </span>
              </td>
              <td class="px-3 py-2">
                <span
                  class="px-2 py-0.5 text-xs font-mono rounded"
                  :class="sample.done ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-gray-700/30 text-gray-500 border border-gray-700'"
                >
                  {{ sample.done ? '是' : '否' }}
                </span>
              </td>
              <td class="px-3 py-2 text-xs font-mono" :style="{ color: 'var(--text-muted)' }">
                {{ new Date(sample.created_at).toLocaleString() }}
              </td>
            </tr>
            <tr v-if="samples.length === 0">
              <td colspan="7" class="px-3 py-8 text-center text-xs font-mono" :style="{ color: 'var(--text-muted)' }">
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
        @change="loadSamples"
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
</template>
