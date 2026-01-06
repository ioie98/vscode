<template>
  <el-card>
    <div slot="header">
      <span style="font-weight: bold; font-size: 16px;">用户管理</span>
    </div>

    <!-- 表格 -->
    <el-table :data="tableData" border stripe style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="账号/学号" width="120" />
      <el-table-column prop="realName" label="姓名" width="100" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.role === 0" type="danger">管理员</el-tag>
          <el-tag v-else-if="row.role === 1">学生</el-tag>
          <el-tag v-else type="warning">维修工</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column label="宿舍信息">
        <template #default="{ row }">
          <span v-if="row.buildingName">{{ row.buildingName }} - {{ row.roomNumber }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="college" label="学院" />
      <el-table-column prop="major" label="专业" />
      <el-table-column prop="className" label="班级" />
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tableData = ref([])

const fetchData = () => {
  axios.get('http://localhost:8080/api/user/list').then(res => {
    if (res.data.code === 200) {
      tableData.value = res.data.data
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>