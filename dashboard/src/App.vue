<script setup lang="ts">
import { RouterView, RouterLink, useRoute } from 'vue-router'

const route = useRoute()

const menuItems = [
  { name: 'Dashboard', title: '仪表盘', path: '/dashboard' },
  { name: 'WhyLog', title: 'Why-Log', path: '/why-log' },
  { name: 'RLSamples', title: 'RL 训练样本', path: '/rl/samples' },
  { name: 'RLCheckpoints', title: 'RL 模型检查点', path: '/rl/checkpoints' },
]

const getIcon = (name: string) => {
  const icons: Record<string, string> = {
    Dashboard: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    WhyLog: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',
    RLSamples: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="12" x2="2" y2="12"></line><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6"></path><path d="M5.45 5.11L22 12"></path></svg>',
    RLCheckpoints: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>',
  }
  return icons[name] || ''
}
</script>

<template>
  <div class="min-h-screen bg-gray-900 flex">
    <aside class="w-64 bg-gray-800 border-r border-gray-700 shrink-0 flex flex-col">
      <div class="p-6 pb-4 border-b border-gray-700">
        <h1 class="text-xl font-mono text-blue-400 tracking-tight font-semibold">Z-Memory</h1>
        <p class="text-xs text-gray-500 mt-1 font-mono">Why-Log & RL Dashboard</p>
      </div>
      <nav class="flex-1 px-2 py-4">
        <RouterLink
          v-for="item in menuItems"
          :key="item.name"
          :to="item.path"
          class="flex items-center gap-2 px-3 py-2 rounded-md text-sm text-gray-400 font-mono transition-all duration-150 mb-0.5 hover:bg-gray-700 hover:text-gray-300"
          :class="{ 'bg-blue-500/10 text-blue-400 border border-blue-500/20': route.path === item.path }"
        >
          <span v-html="getIcon(item.name)" class="w-4 h-4"></span>
          <span>{{ item.title }}</span>
        </RouterLink>
      </nav>
      <div class="p-4 border-t border-gray-700 text-xs text-gray-600 font-mono">
        <div>v1.0.0</div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col min-w-0">
      <header class="sticky top-0 z-40 px-8 py-4 bg-gray-800/50 backdrop-blur-md border-b border-gray-700 shrink-0">
        <h2 class="text-2xl font-mono text-gray-300 tracking-tight font-medium">
          {{ menuItems.find(i => i.path === route.path)?.title || 'Dashboard' }}
        </h2>
        <div class="text-xs text-gray-500 font-mono mt-1">
          /{{ route.path.replace(/^\//, '') || 'dashboard' }}
        </div>
      </header>
      <div class="flex-1 px-8 py-6 overflow-auto">
        <RouterView />
      </div>
    </main>
  </div>
</template>
