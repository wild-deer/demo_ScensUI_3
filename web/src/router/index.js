import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
// 记录路由历史
let routeHistory = []

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/Bhwytj',
      name: 'Bhwytj',
      component: () => import('../views/Bhwytj.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/Wyfwqd',
      name: 'Wyfwqd',
      component: () => import('../views/Wyfwqd.vue'),
    },
    {
      path: '/Gdwytj',
      name: 'Gdwytj',
      component: () => import('../views/Gdwytj.vue'),
    },
    {
      path: '/Pmwytj',
      name: 'Pmwytj',
      component: () => import('../views/Pmwytj.vue'),
    },
  ],
})

export default router
