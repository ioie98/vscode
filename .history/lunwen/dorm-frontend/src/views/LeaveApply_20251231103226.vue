<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <!-- <span style="font-weight: bold; font-size: 16px;">离校/请假申请</span> -->
        <div class="header-actions">
          <el-button v-if="user.role === 1 || user.role === 2" type="primary" icon="Plus"  style="margin-bottom: 10px;"@click="dialogVisible = true">
            提交申请
          </el-button>
          <el-tag v-if="user.role === 0" size="large" style="margin-left: 10px; margin-bottom: 5px;">全校审批</el-tag>
          <el-tag v-else-if="user.role === 1" size="large" type="success" style="margin-left: 10px; margin-bottom: 5px;">本宿舍申请</el-tag>
          <el-tag v-else-if="user.role === 2" size="large" type="warning" style="margin-left: 10px; margin-bottom: 10px;">维修工申请</el-tag>
          <el-button icon="Refresh" circle @click="fetchList" style="margin-left: 10px; margin-bottom: 10px;" />
        </div>
      </div>
      
      <el-table 
        :data="list" 
        style="width: 100%" 
        border 
        stripe
        v-loading="loading"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
        <el-table-column prop="studentName" label="申请人" width="120" /> 
        
        <el-table-column label="类型" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.type === 1 ? 'warning' : 'primary'" size="small">{{ scope.row.type === 1 ? '离校' : '留校' }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="reason" label="原因" show-overflow-tooltip />
        
        <!--起止时间单行显示 -->
        <el-table-column label="起止时间" width="230" align="center">
           <template #default="{row}">
             <span>{{ row.leaveTime ? row.leaveTime.substring(0,10) : '' }}</span>
             <span style="margin: 0 8px; color: #999;">--</span>
             <span>{{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</span>
           </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 1" type="success" size="small">已通过</el-tag>
            <el-tag v-else-if="scope.row.status === 2" type="danger" size="small">已拒绝</el-tag>
            <el-tag v-else type="info" size="small">待审核</el-tag>
          </template>
        </el-table-column>

        <el-table-column v-if="user.role === 0" label="操作" width="180" align="center">
          <template #default="{ row }">
            <div v-if="row.status === 0">
              <el-button type="success" size="small" @click="handleAudit(row, 1)">通过</el-button>
              <el-button type="danger" size="small" @click="handleAudit(row, 2)">拒绝</el-button>
            </div>
            <span v-else style="color:#999">已处理</span>
          </template>
        </el-table-column>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const user = JSON.parse(localStorage.getItem('user') || '{}')
const form = reactive({ type: 1, reason: '', leaveTime: '', returnTime: '' })

// 分页变量
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)

const fetchList = () => {
  loading.value = true
  axios.get(`http://localhost:8080/api/common/leave/list`, {
    params: {
      userId: user.id,
      role: user.role, 
      dormId: user.dormId,
      pageNum: currentPage.value,
      pageSize: pageSize.value
    }
  }).then(res => {
    if(res.data.code === 200) {
      list.value = res.data.data.list
      total.value = res.data.data.total
    }
  }).finally(() => loading.value = false)
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchList()
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
      fetchList()
    } else {
      ElMessage.error('操作失败')
    }
  })
}

onMounted(fetchList)
</script>

<style scoped>
.app-container { padding: 0; background-color: transparent; }
.box-card { min-height: calc(100vh - 100px); border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.el-card__header { border-bottom: 1px solid #ebeef5; padding: 18px 20px; }
</style>