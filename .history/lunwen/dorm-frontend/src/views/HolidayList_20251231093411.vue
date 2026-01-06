<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" style="display: flex; justify-content: flex-start; align-items: center;">
        <div class="header-actions" style="display: flex; align-items: center; gap: 10px;">
          <el-button v-if="user.role === 1" type="primary" icon="Edit" @click="openAddDialog">登记去向</el-button>
          <el-tag v-if="user.role === 1" size="large" type="success">本宿舍去向</el-tag>
          <el-tag v-if="user.role === 0" size="large" type="">全校去向数据</el-tag>
          <el-button icon="Refresh" circle @click="fetchData" />
        </div>
      </div>
        <span>去向筛选：</span>
        <el-select v-model="query" placeholder="全部" style="width: 150px; margin-left: 10px; margin-right: 10px;" @change="fetchData">
          <el-option label="全部" value="全部" /><el-option label="留校" value="留校" /><el-option label="回家" value="回家" /><el-option label="其他" value="其他" />
        </el-select>
        <el-button type="primary" icon="Search" @click="fetchData">查询</el-button>
      </div>

      <el-table :data="tableData" border stripe style="margin-top: 20px;" :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }">
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="major" label="专业" width="120" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column prop="destination" label="去向" align="center"><template #default="{ row }"><el-tag :type="row.destination === '留校' ? 'primary' : 'warning'" size="small">{{ row.destination }}</el-tag></template></el-table-column>
        <el-table-column prop="location" label="具体目的地" />
        <el-table-column prop="returnTime" label="回校时间"><template #default="{row}">{{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</template></el-table-column>
      </el-table>

      <div style="margin-top: 20px; text-align: right;">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="pageSize" @current-change="handleCurrentChange" />
      </div>

      <el-dialog v-model="addDialogVisible" title="登记节假日去向" width="500px">
        <el-form :model="addForm" label-width="100px">
          <el-form-item label="姓名"><el-input v-model="addForm.name" disabled /></el-form-item>
          <el-form-item label="学号"><el-input v-model="addForm.studentId" disabled /></el-form-item>
          <el-form-item label="去向"><el-radio-group v-model="addForm.destination"><el-radio label="留校">留校</el-radio><el-radio label="回家">回家</el-radio><el-radio label="其他">其他</el-radio></el-radio-group></el-form-item>
          <el-form-item label="目的地"><el-input v-model="addForm.location" /></el-form-item>
          <el-form-item label="回校时间"><el-date-picker v-model="addForm.returnTime" type="date" style="width: 100%;" /></el-form-item>
        </el-form>
        <template #footer><el-button @click="addDialogVisible = false">取消</el-button><el-button type="primary" @click="submitAddForm">提交</el-button></template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const query = ref('全部')
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)
const user = JSON.parse(localStorage.getItem('user') || '{}')
const addDialogVisible = ref(false)
const addForm = reactive({ studentId: user.username, name: user.realName, major: user.major || '', className: user.className || '', phone: user.phone || '', destination: '留校', location: '', returnTime: '' })

const fetchData = () => {
  axios.get('http://localhost:8080/api/common/holiday/list', {
    params: { destination: query.value === '全部' ? null : query.value, role: user.role, dormId: user.dormId, pageNum: currentPage.value, pageSize: pageSize.value }
  }).then(res => {
       if(res.data.code === 200) { tableData.value = res.data.data.list; total.value = res.data.data.total }
    })
}
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }
const openAddDialog = () => { addDialogVisible.value = true }
const submitAddForm = () => { axios.post('http://localhost:8080/api/common/holiday/add', addForm).then(res => { if(res.data.code===200){ElMessage.success('登记成功');addDialogVisible.value=false;fetchData()} }) }

onMounted(() => { fetchData() })
</script>
<style scoped> .app-container { padding: 0; background-color: transparent; } .box-card { min-height: calc(100vh - 100px); border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); } </style>