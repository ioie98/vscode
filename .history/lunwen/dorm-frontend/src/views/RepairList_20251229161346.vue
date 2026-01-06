<template>
  <div class="app-container" style="padding: 20px;">
    <!-- 1. 顶部操作栏 -->
    <div class="filter-container" style="margin-bottom: 20px;">
      <!-- 学生可见：新增报修按钮 -->
      <el-button v-if="userRole === 1" type="primary" icon="Plus" @click="handleCreate">我要报修</el-button>
      
      <!-- 维修工/管理员可见：筛选 -->
      <el-checkbox v-if="userRole !== 1" v-model="showOnlyPending" label="只看待处理" @change="fetchData" style="margin-left: 20px;" border />
      
      <el-button icon="Refresh" @click="fetchData" circle style="margin-left: 10px;"></el-button>
    </div>

    <!-- 2. 表格区域 -->
    <el-table :data="tableData" border stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="单号" width="80" align="center" />
      <el-table-column prop="title" label="报修标题" width="180" />
      <el-table-column prop="description" label="故障描述" show-overflow-tooltip />
      
      <el-table-column label="位置" width="150">
        <template #default="scope">
           <!-- 后端如果返回了联表数据，这里显示楼栋+房号 -->
           {{ scope.row.building_name }} {{ scope.row.room_number }}
        </template>
      </el-table-column>

      <el-table-column prop="repairman_name" label="维修师傅" width="120" align="center">
        <template #default="scope">
          <el-tag v-if="scope.row.repairman_name" type="info">{{ scope.row.repairman_name }}</el-tag>
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
      
      <el-table-column label="报修时间" prop="create_time" width="170" />

      <el-table-column label="操作" width="180" fixed="right" align="center">
        <template #default="scope">
          
          <!-- 学生操作: 状态为0(待处理)时可撤销 -->
          <el-button v-if="userRole === 1 && scope.row.status === 0" 
                     size="small" type="danger" icon="Delete" @click="handleDelete(scope.row)">撤销</el-button>

          <!-- 维修工操作: 0可接单, 1可完成 -->
          <template v-if="userRole === 2">
            <el-button v-if="scope.row.status === 0" 
                       size="small" type="success" @click="handleTakeOrder(scope.row)">接单</el-button>
            
            <el-button v-if="scope.row.status === 1 && isMyTask(scope.row)" 
                       size="small" type="primary" @click="handleFinish(scope.row)">维修完成</el-button>
          </template>

          <!-- 管理员操作: 可强制删除 -->
           <el-button v-if="userRole === 0" 
                     size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 3. 报修弹窗 (学生用) -->
    <el-dialog v-model="dialogVisible" title="填写报修单" width="500px">
      <el-form :model="tempRepair" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="tempRepair.title" placeholder="例如：厕所灯泡坏了" />
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input v-model="tempRepair.description" type="textarea" :rows="3" placeholder="请描述具体故障情况..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createData">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 1. 获取用户信息
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const userRole = currentUser.role // 0-管理员, 1-学生, 2-维修工

// 2. 变量定义
const tableData = ref([])
const loading = ref(false)
const showOnlyPending = ref(false)
const dialogVisible = ref(false)
const tempRepair = reactive({
  title: '',
  description: ''
})

// 状态字典
const statusMap = {
  0: { label: '待接单', type: 'danger' },
  1: { label: '维修中', type: 'warning' },
  2: { label: '已完成', type: 'success' }
}

// 3. 核心功能函数

// 获取列表数据
const fetchData = () => {
  loading.value = true
  // 这里暂时用模拟数据，防止你后端没写 RepairController 导致报错
  // 等你写好后端，把这里换成 axios.get('http://localhost:8080/api/repair/list', ...)
  
  // --- 模拟数据开始 ---
  setTimeout(() => {
    const mockData = [
      { id: 101, title: '空调漏水', description: '滴滴答答响', status: 0, create_time: '2025-05-20 10:00', building_name: '8号楼', room_number: '302', repairman_name: null },
      { id: 102, title: '门锁坏了', description: '钥匙打不开', status: 1, create_time: '2025-05-19 14:00', building_name: '8号楼', room_number: '305', repairman_name: '李师傅', repairman_id: 3 }, // 假设当前用户是李师傅(id=3)
      { id: 103, title: '灯管闪烁', description: '快瞎了', status: 2, create_time: '2025-05-18 09:00', building_name: '9号楼', room_number: '101', repairman_name: '王师傅' },
    ]
    
    // 简单的模拟过滤逻辑
    let res = mockData
    if (showOnlyPending.value) {
      res = res.filter(item => item.status === 0)
    }
    tableData.value = res
    loading.value = false
  }, 500)
  // --- 模拟数据结束 ---
}

// 打开报修弹窗 (这就是之前漏掉的函数！)
const handleCreate = () => {
  tempRepair.title = ''
  tempRepair.description = ''
  dialogVisible.value = true
}

// 提交报修数据
const createData = () => {
  if (!tempRepair.title) {
    ElMessage.warning('请填写标题')
    return
  }
  // 模拟提交给后端
  // axios.post('http://localhost:8080/api/repair/add', { ...tempRepair, userId: currentUser.id })...
  
  console.log('提交报修:', tempRepair)
  dialogVisible.value = false
  ElMessage.success('报修提交成功')
  fetchData() // 刷新列表
}

// 撤销/删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要撤销/删除这条报修吗？', '提示', { type: 'warning' }).then(() => {
    ElMessage.success('操作成功')
    // TODO: 调用后端删除接口
    fetchData()
  })
}

// 维修工接单
const handleTakeOrder = (row) => {
  ElMessageBox.confirm('确定接单吗？', '提示').then(() => {
    row.status = 1
    row.repairman_name = currentUser.realName || currentUser.username
    row.repairman_id = currentUser.id
    ElMessage.success('接单成功')
  })
}

// 维修工完成
const handleFinish = (row) => {
  ElMessageBox.confirm('确认已维修完成？', '提示').then(() => {
    row.status = 2
    ElMessage.success('订单已完成')
  })
}

// 判断是否是自己的任务
const isMyTask = (row) => {
  return row.repairman_id === currentUser.id
}

onMounted(() => {
  fetchData()
})
</script>