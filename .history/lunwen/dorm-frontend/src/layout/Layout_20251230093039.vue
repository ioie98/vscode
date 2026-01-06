<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon><School /></el-icon>
        <span>高校宿舍管理系统</span>
      </div>
      
      <el-menu
        active-text-color="#409EFF"
        background-color="#304156"
        text-color="#bfcbd9"
        :default-active="activeMenu"
        router
        class="el-menu-vertical"
      >
        <!-- 模块1：宿舍生活 -->
        <el-sub-menu index="1">
          <template #title>
            <el-icon><HomeFilled /></el-icon>
            <span>宿舍生活</span>
          </template>
          <el-menu-item index="/my-dorm">
            <el-icon><User /></el-icon>我的宿舍
          </el-menu-item>
          <el-menu-item index="/repair">
            <el-icon><Tools /></el-icon>我的报修
          </el-menu-item>
          <!-- 修改：卫生检查，维修工(2)不可见 -->
          <el-menu-item index="/hygiene" v-if="user.role !== 2">
            <el-icon><List /></el-icon>卫生检查
          </el-menu-item>
        </el-sub-menu>

        <!-- 模块2：离返校事务 -->
        <el-sub-menu index="2">
           <template #title>
            <el-icon><Suitcase /></el-icon>
            <span>离返校事务</span>
          </template>
          
          <el-menu-item index="/leave">离校/留校申请</el-menu-item>
          
          <el-menu-item index="/holiday">节假日去向</el-menu-item>

          <!-- 学生专享 -->
          <el-menu-item index="/return-register" v-if="user.role === 1">
             返校登记(学生)
          </el-menu-item>

          <!-- 修改：返校管理，只有管理员(0)可见，维修工看不到了 -->
          <el-menu-item index="/return" v-if="user.role === 0">
             返校管理
          </el-menu-item>
        </el-sub-menu>

        <!-- 模块3：公共区 -->
        <el-menu-item index="/message">
          <el-icon><ChatLineRound /></el-icon>
          <span>留言板</span>
        </el-menu-item>
        
        <!-- 模块4：管理员专区 -->
        <el-menu-item index="/user-list" v-if="user.role === 0">
            <el-icon><UserFilled /></el-icon>
            <span>人员管理</span>
        </el-menu-item>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>

      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon size="20"><Fold /></el-icon>
          <el-breadcrumb separator="/" style="margin-left: 20px;">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRouteName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="el-dropdown-link">
              <el-avatar :size="30" icon="UserFilled" style="margin-right: 8px; vertical-align: middle;" />
              {{ user.realName || user.username }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')

const activeMenu = computed(() => route.path)
const currentRouteName = computed(() => route.meta.title || '当前页面')

const logout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
/* 保持原有样式不变 */
.layout-container { height: 100vh; }
.aside { background-color: #304156; color: white; }
.logo { 
  height: 60px; line-height: 60px; text-align: center; 
  font-size: 18px; font-weight: bold; background: #2b3649;
  display: flex; align-items: center; justify-content: center; gap: 10px;
}
.el-menu-vertical { border-right: none; }
.header { 
  background: #fff; border-bottom: 1px solid #ddd; 
  display: flex; justify-content: space-between; align-items: center;
}
.header-left { display: flex; align-items: center; }
.header-right { cursor: pointer; margin-right: 20px; display: flex; align-items: center;}
.el-dropdown-link { display: flex; align-items: center;}
.main-content { background: #f0f2f5; padding: 20px; }
</style>