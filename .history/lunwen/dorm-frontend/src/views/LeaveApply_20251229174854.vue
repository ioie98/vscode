<template>
  <el-card>
    <div style="margin-bottom: 20px;">
      <!-- 只有学生能提交申请 -->
      <el-button v-if="user.role === 1" type="success" icon="Plus" @click="dialogVisible = true">提交申请</el-button>
      <el-tag v-if="user.role === 0" size="large">离返校申请审批</el-tag>
    </div>
    
    <el-table :data="list" style="width: 100%" border stripe>
      <!-- 管理员特有：显示是谁申请的 -->
      <el-table-column v-if="user.role === 0" prop="studentName" label="申请人" width="120" />
      
      <el-table-column label="类型" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.type === 1 ? 'warning' : 'primary'">{{ scope.row.type === 1 ? '离校' : '留校' }}</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="reason" label="原因" />
      
      <el-table-column label="起止时间" width="220">
         <template #default="{row}">
           <div>{{ row.leaveTime ? row.leaveTime.substring(0,10) : '' }}</div>
           <div>~ {{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</div>
         </template>
      </el-table-column>
      
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 1" type="success">已通过</el-tag>
          <el-tag v-else-if="scope.row.status === 2" type="danger">已拒绝</el-tag>
          <el-tag v-else type="info">待审核</el-tag>
        </template>
      </el-table-column>

      <!-- 管理员操作列 -->
      <el-table-column v-if="user.role === 0" label="操作" width="180">
        <template #default="{ row }">
          <div v-if="row.status === 0">
            <el-button type="success" size="small" @click="handleAudit(row, 1)">通过</el-button>
            <el-button type="danger" size="small" @click="handleAudit(row, 2)">拒绝</el-button>
          </div>
          <span v-else style="color:#999">已处理</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 申请弹窗 -->
    <el-dialog v-model="dialogVisible" title="提交申请" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio :label="1">离校</el-radio>
            <el-radio :label="2">留校</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="form.reason" type="textarea" />
        </el-form-item>
        <el-form-item label="起止时间">
           <el-date-picker v-model="form.leaveTime" type="date" placeholder="开始" style="width: 130px"/>
           - 
           <el-date-picker v-model="form.returnTime" type="date" placeholder="结束" style="width: 130px"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">提交</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const list = ref([])
const dialogVisible = ref(false)
const user = JSON.parse(localStorage.getItem('user') || '{}')
const form = reactive({ type: 1, reason: '', leaveTime: '', returnTime: '' })

const fetchList = () => {
  axios.get(`http://localhost:8080/api/common/leave/list`, {
    params: {
      userId: user.id,
      role: user.role // 关键：把角色传给后端
    }
  }).then(res => {
    if(res.data.code === 200) list.value = res.data.data
  })
}

const submitForm = () => {
  axios.post('http://localhost:8080/api/common/leave/add', {
    ...form,
    userId: user.id
  }).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('提交成功')
      dialogVisible.value = false
      fetchList()
    }
  })
}

// 简单的审核功能 (需要在CommonController加个updateStatus接口，或者这里只是演示前端)
const handleAudit = (row, status) => {
  // 这里暂时模拟成功，实际需要你加一个后端接口
  // axios.post('/api/common/leave/audit', { id: row.id, status })...
  row.status = status
  ElMessage.success(status === 1 ? '已通过' : '已拒绝')
}

onMounted(fetchList)
</script>