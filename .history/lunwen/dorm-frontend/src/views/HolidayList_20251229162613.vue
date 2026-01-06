<template>
  <el-card>
    <div class="filter-header">
      <span>去向筛选：</span>
      <el-select v-model="query" placeholder="全部" style="width: 150px; margin-right: 10px;" @change="fetchData">
        <el-option label="全部" value="全部" />
        <el-option label="留校" value="留校" />
        <el-option label="回家" value="回家" />
      </el-select>
      <el-button type="success" icon="Search" @click="fetchData">查询</el-button>
    </div>

    <el-table :data="tableData" border stripe style="margin-top: 20px;">
      <el-table-column prop="studentId" label="学号" width="120" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="major" label="专业" width="120" />
      <el-table-column prop="destination" label="去向" align="center">
        <template #default="{ row }">
          <el-tag :type="row.destination === '留校' ? 'primary' : 'warning'">{{ row.destination }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="location" label="具体目的地" />
      <el-table-column prop="returnTime" label="回校时间">
         <template #default="{row}">{{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const query = ref('全部')
const tableData = ref([])

const fetchData = () => {
  axios.get(`http://localhost:8080/api/common/holiday/list?destination=${query.value}`)
    .then(res => {
       if(res.data.code === 200) tableData.value = res.data.data
    })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped> .filter-header { display: flex; align-items: center; } </style>