<template>
  <el-card>
    <div style="margin-bottom: 20px;">
      <el-button type="success" icon="Plus" @click="dialogVisible = true">提交申请</el-button>
    </div>
    
    <el-table :data="list" style="width: 100%" border>
      <el-table-column label="类型" width="100">
        <template #default="scope">
          <el-tag>{{ scope.row.type === 1 ? '离校' : '留校' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="原因" />
      <el-table-column prop="leaveTime" label="开始时间" width="180">
         <template #default="{row}">{{ row.leaveTime?.substring(0,10) }}</template>
      </el-table-column>
      <el-table-column prop="returnTime" label="结束时间" width="180">
         <template #default="{row}">{{ row.returnTime?.substring(0,10) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">
            {{ scope.row.status === 1 ? '已通过' : '审核中' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <!-- 简单的新增弹窗 -->
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
           <el-date-picker v-model="form.leaveTime" type="date" placeholder="开始日期" style="width: 150px"/>
           - 
           <el-date-picker v-model="form.returnTime" type="date" placeholder="结束日期" style="width: 150px"/>
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
  axios.get(`http://localhost:8080/api/common/leave/list?userId=${user.id}`).then(res => {
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

onMounted(fetchList)
</script>