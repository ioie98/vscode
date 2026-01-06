import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import RepairList from '../views/RepairList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login' // 默认跳转到登录
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/repair',
      name: 'RepairList',
      component: RepairList,
      // 简单的路由守卫：没登录不让进
      beforeEnter: (to, from, next) => {
        const user = localStorage.getItem('user')
        if (!user) {
          next('/login')
        } else {
          next()
        }
      }
    }
  ]
})

export default router