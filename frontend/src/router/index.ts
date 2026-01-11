import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/DashboardView.vue'),
    },
    {
      path: '/why-log',
      name: 'WhyLog',
      component: () => import('../views/WhyLogView.vue'),
    },
    {
      path: '/rl/samples',
      name: 'RLSamples',
      component: () => import('../views/RLSamplesView.vue'),
    },
    {
      path: '/rl/checkpoints',
      name: 'RLCheckpoints',
      component: () => import('../views/RLCheckpointsView.vue'),
    },
  ],
})

export default router
