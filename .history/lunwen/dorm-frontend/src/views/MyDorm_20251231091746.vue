<template>
  <div class="app-container">
    <el-card class="box-card">
      <!-- 头部：移除标题，将操作元素靠左对齐 -->
      <div slot="header" class="clearfix" style="display: flex; align-items: center;">
        <div class="header-actions" style="display: flex; align-items: center; gap: 10px;">
          <!-- 1. 角色标识/按钮 -->
          <el-button type="success" icon="Check" v-if="currentUser.role === 1">我的床位</el-button>
          <el-tag v-if="currentUser.role === 0" size="small" effect="dark">全校学生住宿总览</el-tag>
          
          <!-- 2. 刷新按钮 (紧跟在后面) -->
          <el-button icon="Refresh" circle @click="fetchData" />
        </div>
      </div>

      <!-- 表格区域 -->
      <el-table 
        :data="tableData" 
        style="width: 100%" 
        stripe 
        border 
        v-loading="loading"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
        <el-table-column prop="zoneName" label="宿舍区" width="120" />
        <el-table-column prop="buildingName" label="楼栋" width="100" />
        <el-table-column prop="roomNumber" label="寝室" width="100" />
        <el-table-column prop="bedNum" label="床位号" width="80" align="center" />
        <el-table-column prop="realName" label="姓名" width="120" />
        <el-table-column prop="username" label="学号" width="150" />
        <el-table-column prop="college" label="学院" width="150" />
        <el-table-column prop="major" label="专业" width="150" />
        <el-table-column prop="className" label="班级" />
      </el-table>

      <!-- 分页组件 -->
      <div style="margin-top: 20px; text-align: right;">
        <el-pagination 
          background 
          layout="total, prev, pager, next, sizes, jumper" 
          :total="total" 
          :page-sizes="[10, 20, 50, 100]" 
          :page-size="pageSize" 
          @size-change="handleSizeChange" 
          @current-change="handleCurrentChange" 
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tableData = ref([])
const loading = ref(false)
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')

// 分页变量
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const fetchData = () => {
  // 只有当是学生且没有分配宿舍时，才清空并不请求
  if (currentUser.role === 1 && !currentUser.dormId) {
    tableData.value = []; 
    return
  }
  
  loading.value = true
  // 请确保IP地址正确
  axios.get(`http://192.168.12.26:8080/api/my-dorm/list`, { 
    params: {
      dormId: currentUser.dormId,
      role: currentUser.role,
      pageNum: currentPage.value,
      pageSize: pageSize.value
    }
  }).then(res => {
      if (res.data.code === 200) {
        // 解析分页结构 { total, list }
        tableData.value = res.data.data.list
        total.value = res.data.data.total
      }
    })
    .finally(() => loading.value = false)
}

// 分页事件处理
const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.app-container {
  padding: 0; 
  background-color: transparent; 
}
.box-card {
  min-height: calc(100vh - 100px); 
  border-radius: 8px; 
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); 
}
.clearfix:before, .clearfix:after {
  display: table;
  content: "";
}
.clearfix:after {
  clear: both
}
.el-card__header {
  border-bottom: 1px solid #ebeef5; 
  padding: 18px 20px;
}
/* 确保 flex 布局生效 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>