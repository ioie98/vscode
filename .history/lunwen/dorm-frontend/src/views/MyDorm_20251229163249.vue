<template>
  <el-card class="box-card">
    <!-- 顶部操作 -->
    <div style="margin-bottom: 20px;">
      <el-button type="success" icon="Check">选择床位</el-button>
      <div style="float: right;">
        <el-button icon="Grid" circle />
        <el-button icon="Download" circle />
        <el-button icon="Printer" circle />
      </div>
    </div>

    <!-- 
      修复点：
      1. :header-cell-style="{ background: '#f5f7fa' }" 
         (之前写的是字符串 "background...", 现在改成了对象绑定写法)
    -->
    <el-table 
      :data="tableData" 
      style="width: 100%" 
      stripe 
      :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
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

    <!-- 分页 (模拟) -->
    <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
      <el-pagination background layout="prev, pager, next" :total="tableData.length || 0" :page-size="10" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const tableData = ref([])
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')

const fetchData = () => {
  if (!currentUser.dormId) {
    // 如果没有 dormId，说明还没分配宿舍或者缓存没更新
    return
  }
  
  axios.get(`http://localhost:8080/api/my-dorm/list?dormId=${currentUser.dormId}`)
    .then(res => {
      if (res.data.code === 200) {
        // 注意：后端开启了 map-underscore-to-camel-case=true
        // 所以数据库的 zone_name 会变成 zoneName，building_name 变成 buildingName
        tableData.value = res.data.data
      }
    })
    .catch(err => {
      console.error(err)
    })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.box-card {
  min-height: 500px;
}
</style>