<template>
  <div class="app-container" style="padding: 20px;">
    <!-- 顶部操作栏 -->
    <div class="filter-container" style="margin-bottom: 20px;">
      <el-button v-if="userRole === 1" type="primary" icon="Plus" @click="handleCreate">我要报修</el-button>
      <el-checkbox v-if="userRole !== 1" v-model="showOnlyPending" label="只看待处理" @change="fetchData" style="margin-left: 20px;" border />
      <el-button icon="Refresh" @click="fetchData" circle style="margin-left: 10px;"></el-button>
    </div>

    <!-- 表格 -->
    <el-table :data="tableData" border stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="单号" width="80" align="center" />
      <el-table-column prop="title" label="报修标题" width="150" />
      <el-table-column prop="description" label="故障描述" show-overflow-tooltip />
      
      <!-- 报修人姓名 -->
      <el-table-column prop="studentName" label="报修人" width="100" /> 
      
      <el-table-column label="位置" width="120">
        <template #default="scope">
           {{ scope.row.buildingName }} {{ scope.row.roomNumber }}
        </template>
      </el-table-column>
      
      <el-table-column prop="repairmanName" label="维修师傅" width="120" align="center">
        <template #default="scope">
          <el-tag v-if="scope.row.repairmanName" type="info">{{ scope.row.repairmanName }}</el-tag>
          <span v-else style="color: #999;">待指派</span>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="100" align="center">
        <template #default="scope">
          <el-tag :type="statusMap[scope.row.status]?.type">
            {{ statusMap[scope.row.status]?.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="报修时间" width="160">
        <template #default="{row}">{{ row.createTime ? row.createTime.replace('T',' ').substring(0,16) : '' }}</template>
      </el-table-column>

      <el-table-column label="操作" width="200" fixed="right" align="center">
        <template #default="scope">
          
          <!-- 学生操作: 仅待处理状态可撤销/删除 (只能撤销自己的) -->
          <el-button 
            v-if="userRole === 1 && scope.row.status === 0 && scope.row.userId === currentUser.id" 
            size="small" type="danger" icon="Delete" @click="handleDelete(scope.row)">撤销</el-button>

          <!-- 维修工操作 -->
          <template v-if="userRole === 2">
            <el-button v-if="scope.row.status === 0" 
                       size="small" type="success" @click="handleTakeOrder(scope.row)">接单</el-button>
            <el-button v-if="scope.row.status === 1 && isMyTask(scope.row)" 
                       size="small" type="primary" @click="handleFinish(scope.row)">完成</el-button>
          </template>

          <!-- 管理员操作 -->
           <template v-if="userRole === 0">
             <el-button v-if="scope.row.status === 0" size="small" type="warning" @click="openAssignDialog(scope.row)">指派</el-button>
             <el-button size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
           </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 1. 学生报修弹窗 -->
    <el-dialog v-model="dialogVisible" title="填写报修单" width="500px">
      <el-form :model="tempRepair" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="tempRepair.title" placeholder="例如：厕所灯泡坏了" />
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input v-model="tempRepair.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createData">提交</el-button>
      </template>
    </el-dialog>

    <!-- 2. 管理员指派弹窗 -->
    <el-dialog v-model="assignDialogVisible" title="指派维修师傅" width="400px">
      <div style="margin-bottom: 20px;">请为单号 <b>{{ currentRepairId }}</b> 选择维修人员：</div>
      <el-select v-model="selectedRepairmanId" placeholder="请选择维修工" style="width: 100%">
        <el-option
          v-for="item in repairmanList"
          :key="item.id"
          :label="item.realName + ' (' + item.phone + ')'"
          :value="item.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAssign">确认指派</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const userRole = currentUser.role 
const tableData = ref([])
const loading = ref(false)
const showOnlyPending = ref(false)

const dialogVisible = ref(false)
const tempRepair = reactive({ title: '', description: '' })

const assignDialogVisible = ref(false)
const repairmanList = ref([])
const selectedRepairmanId = ref(null)
const currentRepairId = ref(null)

const statusMap = {
  0: { label: '待处理', type: 'danger' },
  1: { label: '维修中', type: 'warning' },
  2: { label: '已完成', type: 'success' }
}

const fetchData = () => {
  loading.value = true
  const params = {
    role: userRole,
    dormId: userRole === 1 ? currentUser.dormId : null // 学生才传 dormId，管理员和维修工不传
  }
  
  axios.get('http://localhost:8080/api/repair/list', { params })
    .then(res => {
      if (res.data.code === 200) {
        let list = res.data.data
        if (showOnlyPending.value) list = list.filter(item => item.status === 0)
        tableData.value = list
      }
    })
    .finally(() => loading.value = false)
}

const createData = () => {
  if (!tempRepair.title) return ElMessage.warning('请填写标题')
  axios.post('http://localhost:8080/api/repair/add', {
    title: tempRepair.title,
    description: tempRepair.description,
    userId: currentUser.id,
    dormId: currentUser.dormId
  }).then(res => {
    if (res.data.code === 200) {
      ElMessage.success('报修成功')
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(res.data.msg)
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除/撤销吗？', '提示', { type: 'warning' }).then(() => {
    axios.post('http://localhost:8080/api/repair/delete', { id: row.id }).then(res => {
       ElMessage.success('删除成功')
       fetchData()
    })
  })
}

const openAssignDialog = (row) => {
  currentRepairId.value = row.id
  selectedRepairmanId.value = null
  assignDialogVisible.value = true
  
  axios.get('http://localhost:8080/api/user/repairmen').then(res => {
    if(res.data.code === 200) {
      repairmanList.value = res.data.data
    }
  })
}

const submitAssign = () => {
  if (!selectedRepairmanId.value) return ElMessage.warning('请选择维修工')
  
  axios.post('http://localhost:8080/api/repair/assign', {
    id: currentRepairId.value,
    repairmanId: selectedRepairmanId.value
  }).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('指派成功')
      assignDialogVisible.value = false
      fetchData()
    }
  })
}

const handleTakeOrder = (row) => {
  ElMessageBox.confirm('确定接单吗？', '提示').then(() => {
    axios.post('http://localhost:8080/api/repair/take', { id: row.id, repairmanId: currentUser.id }).then(res => {
      ElMessage.success('接单成功'); fetchData()
    })
  })
}
const handleFinish = (row) => {
  ElMessageBox.confirm('确认已维修完成？', '提示').then(() => {
    axios.post('http://localhost:8080/api/repair/finish', { id: row.id }).then(res => {
      ElMessage.success('订单已完成'); fetchData()
    })
  })
}

const handleCreate = () => {
  if (!currentUser.dormId) { // 如果学生未分配宿舍，禁止报修
    ElMessage.warning('您暂未分配宿舍，无法提交报修')
    return
  }
  tempRepair.title = ''; tempRepair.description = ''; dialogVisible.value = true
}

const isMyTask = (row) => { return row.repairmanId === currentUser.id }

onMounted(() => {
  fetchData()
})
</script>