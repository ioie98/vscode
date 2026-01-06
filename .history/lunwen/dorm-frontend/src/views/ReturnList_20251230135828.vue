<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">学生返校管理</span>
        <div class="header-actions">
          <el-button type="success" icon="Download">导出名单</el-button>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px;" />
        </div>
      </div>
      
      <el-table 
        :data="tableData" 
        border 
        stripe
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="returnTime" label="返校日期" width="120">
          <template #default="{row}">{{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</template>
        </el-table-column>
        <el-table-column prop="isDelayed" label="是否延迟" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isDelayed === '是' ? 'danger' : 'success'" size="small">{{ row.isDelayed }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="延迟原因" show-overflow-tooltip />
        <el-table-column prop="transport" label="交通方式" width="100" />
        <el-table-column prop="transportNo" label="车次/航班号" width="120" />
      </el-table>

      <div v-if="tableData.length === 0" style="text-align: center; color: #999; margin-top: 20px;">
        暂无返校记录
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tableData = ref([])

const fetchData = () => {
  axios.get('http://localhost:8080/api/common/return/list').then(res => {
    if(res.data.code === 200) tableData.value = res.data.data
  }).catch(err => {
    console.error("获取返校管理数据失败:", err);
    ElMessage.error("加载数据失败，请检查网络或控制台错误");
  });
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