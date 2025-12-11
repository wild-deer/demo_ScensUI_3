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
      path: '/structure-recognition',
      name: 'StructureRecognition',
      component: () => import('../views/StructureRecognition.vue'),
    },
    {
      path: '/icon-gallery',
      name: 'IconGallery',
      component: () => import('../views/IconGallery.vue'),
    },
  ],
})

export default router
