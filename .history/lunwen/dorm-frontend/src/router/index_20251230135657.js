import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/Login.vue'
import Layout from '../layout/Layout.vue'
import RepairList from '../views/RepairList.vue'
import MyDorm from '../views/MyDorm.vue'
import HygieneList from '../views/HygieneList.vue'
import LeaveApply from '../views/LeaveApply.vue'
import MessageBoard from '../views/MessageBoard.vue'
import HolidayList from '../views/HolidayList.vue'
import ReturnList from '../views/ReturnList.vue'
import ReturnRegister from '../views/ReturnRegister.vue'
import Settings from '../views/Settings.vue'
import UserList from '../views/UserList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/',
      component: Layout, 
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
        { 
          path: '/hygiene', 
          component: HygieneList, 
          meta: { title: '卫生检查记录' } 
        },
        { 
          path: '/leave', 
          component: LeaveApply, 
          meta: { title: '离校/请假申请' } 
        },
        { 
          path: '/message', 
          component: MessageBoard, 
          meta: { title: '留言板' } 
        },
        { 
          path: '/holiday', 
          component: HolidayList, 
          meta: { title: '节假日去向管理' } 
        },
        { 
          path: '/return', 
          component: ReturnList, 
          meta: { title: '学生返校管理' } 
        },
        { 
          path: '/return-register', 
          component: ReturnRegister, 
          meta: { title: '返校登记' } 
        },
        { 
          path: '/settings', 
          component: Settings, 
          meta: { title: '个人设置' } 
        },
        { 
          path: '/user-list', 
          component: UserList, 
          meta: { title: '用户管理' } 
        },
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const user = localStorage.getItem('user')
  if (to.path !== '/login' && !user) {
    next('/login')
  } else {
    next()
  }
})

export default router