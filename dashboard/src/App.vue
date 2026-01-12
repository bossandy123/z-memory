<script setup lang="ts">
import { RouterView, RouterLink, useRoute } from 'vue-router'
import ThemeToggle from './components/ThemeToggle.vue'

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
  <div class="min-h-screen flex" :style="{ backgroundColor: 'var(--bg-primary)' }">
    <aside class="w-64 border-r shrink-0 flex flex-col" :style="{ backgroundColor: 'var(--sidebar-bg)', borderColor: 'var(--border-color)' }">
      <div class="p-6 pb-4 border-b" :style="{ borderColor: 'var(--border-color)' }">
        <h1 class="text-xl font-mono text-blue-400 tracking-tight font-semibold">Z-Memory</h1>
        <p class="text-xs mt-1 font-mono" :style="{ color: 'var(--text-muted)' }">Why-Log & RL Dashboard</p>
      </div>
      <nav class="flex-1 px-2 py-4">
        <RouterLink
          v-for="item in menuItems"
          :key="item.name"
          :to="item.path"
          class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-mono transition-all duration-150 mb-0.5"
          :style="{ color: 'var(--text-secondary)' }"
          :class="{ 'bg-blue-500/10 text-blue-400 border border-blue-500/20': route.path === item.path, 'hover:bg-gray-700': route.path !== item.path }"
        >
          <span v-html="getIcon(item.name)" class="w-4 h-4" :style="{ color: route.path === item.path ? '' : 'inherit' }"></span>
          <span>{{ item.title }}</span>
        </RouterLink>
      </nav>
      <div class="p-4 border-t text-xs font-mono" :style="{ borderColor: 'var(--border-color)', color: 'var(--text-muted)' }">
        <div>v1.0.0</div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col min-w-0">
      <header class="sticky top-0 z-40 px-8 py-4 backdrop-blur-md border-b shrink-0 flex items-center justify-between" :style="{ backgroundColor: 'var(--header-bg)', borderColor: 'var(--border-color)' }">
        <div>
          <h2 class="text-2xl font-mono tracking-tight font-medium" :style="{ color: 'var(--text-primary)' }">
            {{ menuItems.find(i => i.path === route.path)?.title || 'Dashboard' }}
          </h2>
          <div class="text-xs font-mono mt-1" :style="{ color: 'var(--text-muted)' }">
            /{{ route.path.replace(/^\//, '') || 'dashboard' }}
          </div>
        </div>
        <ThemeToggle />
      </header>
      <div class="flex-1 px-8 py-6 overflow-auto">
        <RouterView />
      </div>
    </main>
  </div>
</template>
