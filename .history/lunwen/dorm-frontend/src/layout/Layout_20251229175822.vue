<template>
  <el-container class="layout-container">
    <!-- 左侧菜单栏 -->
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
        <!-- 模块1：宿舍生活 (通用) -->
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
          <el-menu-item index="/hygiene">
            <el-icon><List /></el-icon>卫生检查
          </el-menu-item>
        </el-sub-menu>

        <!-- 模块2：离返校事务 (整合了之前写的所有相关页面) -->
        <el-sub-menu index="2">
           <template #title>
            <el-icon><Suitcase /></el-icon>
            <span>离返校事务</span>
          </template>
          
          <!-- 通用：请假申请 -->
          <el-menu-item index="/leave">离校/请假申请</el-menu-item>
          
          <!-- 通用：节假日去向 -->
          <el-menu-item index="/holiday">节假日去向</el-menu-item>

          <!-- 学生专享：返校登记 -->
          <el-menu-item index="/return-register" v-if="user.role === 1">
             返校登记(学生)
          </el-menu-item>

          <!-- 管理员专享：返校管理列表 -->
          <el-menu-item index="/return" v-if="user.role === 0">
             返校管理(管理员)
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

        <!-- 模块5：个人设置 -->
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>

      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶部 Header -->
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

      <!-- 主内容区域 -->
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
// 加上 || '{}' 防止报错
const user = JSON.parse(localStorage.getItem('user') || '{}')

const activeMenu = computed(() => route.path)
const currentRouteName = computed(() => route.meta.title || '当前页面')

const logout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.layout-container { height: 100vh; }
.aside { background-color: #304156; color: white; transition: width 0.3s; }
.logo { 
  height: 60px; line-height: 60px; text-align: center; 
  font-size: 18px; font-weight: bold; background: #2b3649;
  display: flex; align-items: center; justify-content: center; gap: 10px;
  overflow: hidden;
}
.el-menu-vertical { border-right: none; }
.header { 
  background: #fff; border-bottom: 1px solid #e6e6e6; 
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}
.header-left { display: flex; align-items: center; }
.header-right { cursor: pointer; margin-right: 20px; display: flex; align-items: center;}
.el-dropdown-link { display: flex; align-items: center; font-weight: 500;}
.main-content { background: #f0f2f5; padding: 20px; }
</style>