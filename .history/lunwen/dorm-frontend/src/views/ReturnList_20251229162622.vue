<template>
  <el-card>
    <el-button type="primary" style="margin-bottom: 20px;">导出名单</el-button>
    
    <el-table :data="tableData" border stripe>
      <el-table-column prop="studentId" label="学号" width="120" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="returnTime" label="返校日期" width="120">
         <template #default="{row}">{{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</template>
      </el-table-column>
      <el-table-column prop="isDelayed" label="是否延迟" width="100">
        <template #default="{ row }">
          <el-tag :type="row.isDelayed === '是' ? 'danger' : 'success'">{{ row.isDelayed }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="延迟原因" />
      <el-table-column prop="transport" label="交通方式" width="100" />
      <el-table-column prop="transportNo" label="车次/航班" width="120" />
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tableData = ref([])

onMounted(() => {
  axios.get('http://localhost:8080/api/common/return/list').then(res => {
    if(res.data.code === 200) tableData.value = res.data.data
  })
})
</script>