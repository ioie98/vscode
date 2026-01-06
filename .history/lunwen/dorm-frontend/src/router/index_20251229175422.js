import { createRouter, createWebHistory } from 'vue-router'

// 1. 引入所有页面组件
import Login from '../views/Login.vue'
import Layout from '../layout/Layout.vue'
import RepairList from '../views/RepairList.vue'
import MyDorm from '../views/MyDorm.vue'
import HygieneList from '../views/HygieneList.vue'      // 卫生检查
import LeaveApply from '../views/LeaveApply.vue'        // 离返校申请
import MessageBoard from '../views/MessageBoard.vue'    // 留言板
import HolidayList from '../views/HolidayList.vue'      // 节假日去向
import ReturnList from '../views/ReturnList.vue'        // 返校管理
import Settings from '../views/Settings.vue'            // 设置
import UserList from '../views/UserList.vue'          // 用户列表（管理员专用）
import ReturnRegister from '../views/ReturnRegister.vue'

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
      component: Layout, // 使用侧边栏布局作为父路由
      redirect: '/my-dorm', // 登录后默认去我的宿舍
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
          meta: { title: '离返校/请假申请' } 
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

// 路由守卫：没登录就踢回登录页
router.beforeEach((to, from, next) => {
  const user = localStorage.getItem('user')
  if (to.path !== '/login' && !user) {
    next('/login')
  } else {
    next()
  }
})

export default router