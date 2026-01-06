<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <!-- <span style="font-weight: bold; font-size: 16px;">学生返校管理</span> -->
        <div class="header-actions">
          <!-- 修改点：绑定点击事件 handleExport -->
          <el-button type="success" icon="Download" style="margin-bottom: 10px;" @click="handleExport" :loading="exportLoading">导出名单</el-button>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px; margin-bottom: 10px;" />
        </div>
      </div>
      
      <el-table 
        :data="tableData" 
        border 
        stripe
        v-loading="loading"
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

      <!-- 分页组件 -->
      <div style="margin-top: 20px; text-align: right;">
        <el-pagination 
          background 
          layout="total, prev, pager, next" 
          :total="total" 
          :page-size="pageSize" 
          @current-change="handleCurrentChange" 
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx' // 引入 xlsx 库

const tableData = ref([])
const loading = ref(false)
const exportLoading = ref(false) // 导出按钮的加载状态
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)

// 获取列表数据
const fetchData = () => {
  loading.value = true
  axios.get('http://192.168.12.26:8080/api/common/return/list', { // 请确保IP正确
    params: {
      pageNum: currentPage.value,
      pageSize: pageSize.value
    }
  }).then(res => {
    if(res.data.code === 200) {
      tableData.value = res.data.data.list
      total.value = res.data.data.total
    }
  }).catch(err => {
    console.error("获取返校管理数据失败:", err);
    ElMessage.error("加载数据失败");
  }).finally(() => loading.value = false)
}

// 导出 Excel 的核心逻辑
const handleExport = () => {
  exportLoading.value = true
  
  // 1. 请求所有数据 
  // 复用 list 接口
  axios.get('http://192.168.12.26:8080/api/common/return/list', {
    params: {
      pageNum: 1,
      pageSize: 10000 
    }
  }).then(res => {
    if (res.data.code === 200) {
      const allList = res.data.data.list
      
      // 2. 数据格式转换：将英文字段转为中文表头
      const exportData = allList.map(item => {
        return {
          '学号': item.studentId,
          '姓名': item.name,
          '返校日期': item.returnTime ? item.returnTime.substring(0, 10) : '',
          '是否延迟': item.isDelayed,
          '延迟原因': item.reason || '无',
          '交通方式': item.transport,
          '车次/航班号': item.transportNo
        }
      })

      // 3. 生成 Excel
      // 创建一个工作簿
      const wb = XLSX.utils.book_new()
      // 将 JSON 数据转换成工作表
      const ws = XLSX.utils.json_to_sheet(exportData)
      // 将工作表添加到工作簿，命名为 "返校名单"
      XLSX.utils.book_append_sheet(wb, ws, '返校名单')
      
      // 4. 下载文件
      XLSX.writeFile(wb, '学生返校登记名单.xlsx')
      
      ElMessage.success('导出成功')
    } else {
      ElMessage.error('导出失败：无法获取数据')
    }
  }).catch(err => {
    console.error(err)
    ElMessage.error('导出出错')
  }).finally(() => {
    exportLoading.value = false
  })
}

const handleCurrentChange = (val) => {
  currentPage.value = val
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
.el-card__header {
  border-bottom: 1px solid #ebeef5; 
  padding: 18px 20px;
}
</style>