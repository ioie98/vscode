<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">宿舍信息概览</span>
        <div class="header-actions">
          <el-button type="success" icon="Check" v-if="currentUser.role === 1">我的床位</el-button>
          <el-tag v-if="currentUser.role === 0" size="large" effect="dark">全校学生住宿总览</el-tag>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px;" />
        </div>
      </div>

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
  if (currentUser.role === 1 && !currentUser.dormId) {
    tableData.value = []; 
    return
  }
  
  loading.value = true
  axios.get(`http://localhost:8080/api/my-dorm/list`, { // 请确保使用正确的IP
    params: {
      dormId: currentUser.dormId,
      role: currentUser.role,
      pageNum: currentPage.value, // 传分页参数
      pageSize: pageSize.value
    }
  }).then(res => {
      if (res.data.code === 200) {
        // 解析分页结构
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
</style>