<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">节假日去向统计</span>
        <div class="header-actions">
          <el-tag v-if="user.role === 1" type="success" style="margin-right: 10px">本宿舍</el-tag>
          <el-tag v-if="user.role === 0" type="danger" style="margin-right: 10px">全校数据</el-tag>
          <el-tag v-if="user.role === 2" type="warning" style="margin-right: 10px">维修工去向</el-tag>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px;" />
        </div>
      </div>

      <div class="filter-header" style="padding-bottom: 15px; border-bottom: 1px dashed #eee;">
        <span>去向筛选：</span>
        <el-select v-model="query" placeholder="全部" style="width: 150px; margin-right: 10px;" @change="fetchData">
          <el-option label="全部" value="全部" />
          <el-option label="留校" value="留校" />
          <el-option label="回家" value="回家" />
        </el-select>
        <el-button type="primary" icon="Search" @click="fetchData">查询</el-button>
      </div>

      <el-table 
        :data="tableData" 
        border 
        stripe 
        style="margin-top: 20px;"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="major" label="专业" width="120" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column prop="destination" label="去向" align="center">
          <template #default="{ row }">
            <el-tag :type="row.destination === '留校' ? 'primary' : 'warning'" size="small">{{ row.destination }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="具体目的地" />
        <el-table-column prop="returnTime" label="回校时间">
          <template #default="{row}">{{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</template>
        </el-table-column>
      </el-table>

      <div v-if="tableData.length === 0" style="text-align: center; color: #999; margin-top: 20px;">
        暂无数据
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const query = ref('全部')
const tableData = ref([])
const user = JSON.parse(localStorage.getItem('user') || '{}')

const fetchData = () => {
  axios.get(`http://localhost:8080/api/common/holiday/list`, {
    params: {
      destination: query.value === '全部' ? null : query.value,
      role: user.role,     
      dormId: user.dormId  
    }
  }).then(res => {
       if(res.data.code === 200) tableData.value = res.data.data
    }).catch(err => {
      console.error("获取节假日去向失败:", err);
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
.filter-header { 
  display: flex; 
  align-items: center; 
} 
</style>