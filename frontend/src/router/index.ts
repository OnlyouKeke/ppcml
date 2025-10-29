import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'report',
    component: () => import('../views/ReportBuilder.vue'),
    meta: {
      title: '宠物检测报告'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || '宠物检测报告'} - Electron + FastAPI + Vue3`
  next()
})

export default router
