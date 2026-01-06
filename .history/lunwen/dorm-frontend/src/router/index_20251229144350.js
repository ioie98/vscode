import { createRouter, createWebHistory } from 'vue-router'
// 引入刚才新建的组件
import RepairList from '../views/RepairList.vue' 

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/repair' // 默认跳转到报修页
    },
    {
      path: '/repair',
      name: 'repair',
      component: RepairList
    }
  ]
})

export default router