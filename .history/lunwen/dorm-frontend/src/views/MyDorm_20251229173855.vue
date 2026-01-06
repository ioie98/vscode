<template>
  <el-card class="box-card">
    <div style="margin-bottom: 20px;">
      <!-- 根据角色显示不同标题 -->
      <el-button type="success" icon="Check" v-if="currentUser.role === 1">我的床位</el-button>
      <el-tag v-if="currentUser.role === 0" size="large" effect="dark">全校学生住宿总览</el-tag>

      <div style="float: right;">
        <el-button icon="Refresh" circle @click="fetchData" />
      </div>
    </div>

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

    <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
      <el-pagination background layout="prev, pager, next" :total="tableData.length" :page-size="10" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tableData = ref([])
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')

const fetchData = () => {
  // 逻辑修改：只有当是普通学生(role=1)且没有宿舍ID时，才拦截。管理员(role=0)直接放行。
  if (currentUser.role === 1 && !currentUser.dormId) {
    return
  }
  
  // 传参增加 role
  axios.get(`http://localhost:8080/api/my-dorm/list`, {
    params: {
      dormId: currentUser.dormId,
      role: currentUser.role
    }
  }).then(res => {
      if (res.data.code === 200) {
        tableData.value = res.data.data
      }
    })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.box-card { min-height: 500px; }
</style>