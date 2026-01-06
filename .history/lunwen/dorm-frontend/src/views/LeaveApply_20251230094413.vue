<template>
  <el-card>
    <div style="margin-bottom: 20px;">
      <!-- 修改点1：学生(1) 和 维修工(2) 都能提交申请 -->
      <el-button v-if="user.role === 1 || user.role === 2" type="success" icon="Plus" @click="dialogVisible = true">
        提交申请
      </el-button>
      
      <el-tag v-if="user.role === 0" size="large">离返校申请审批</el-tag>
    </div>
    
    <el-table :data="list" style="width: 100%" border stripe>
      <!-- 修改点2：管理员(0) 和 维修工(2) 都能看到是谁申请的 -->
      <el-table-column v-if="user.role === 0 || user.role === 2" prop="studentName" label="申请人" width="120" />
      
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

      <!-- 修改点3：只有管理员(0) 能进行审核操作，维修工只能看不能审 -->
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
      role: user.role 
    }
  }).then(res => {
    if(res.data.code === 200) list.value = res.data.data
  })
}

const submitForm = () => {
  if(!form.reason || !form.leaveTime) return ElMessage.warning('请填写完整')
  
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

const handleAudit = (row, status) => {
  axios.post('http://localhost:8080/api/common/leave/audit', {
    id: row.id,
    status: status
  }).then(res => {
    if (res.data.code === 200) {
      ElMessage.success(status === 1 ? '已通过' : '已拒绝')
      // 审核成功后，重新从数据库拉取最新数据，确保状态同步
      fetchList()
    } else {
      ElMessage.error('操作失败')
    }
  })
}

onMounted(fetchList)
</script>