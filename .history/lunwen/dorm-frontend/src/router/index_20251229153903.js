import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../layout/Layout.vue' // 引入布局
import RepairList from '../views/RepairList.vue'
// 下面这个稍后创建
import MyDorm from '../views/MyDorm.vue' 

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', component: Login },
    {
      path: '/',
      component: Layout, // 使用布局组件
      redirect: '/my-dorm',
      children: [
        { 
          path: '/my-dorm', 
          component: MyDorm, 
          meta: { title: '我的宿舍' } 
        },
        { 
          path: '/repair', 
          component: RepairList, 
          meta: { title: '我的报修' } 
        },
        // 这里可以继续添加 卫生、离校、留言板 的路由
        { path: '/hygiene', component: { template: '<h1>卫生检查页面(开发中)</h1>' }, meta: { title: '卫生检查' } },
        { path: '/leave', component: { template: '<h1>离返校登记(开发中)</h1>' }, meta: { title: '离返校' } },
        { path: '/message', component: { template: '<h1>留言板(开发中)</h1>' }, meta: { title: '留言板' } },
      ]
    }
  ]
})

export default router