<template>
  <div class="app-container">
    <div class="filter-container" style="margin-bottom: 20px;">
      <!-- 学生可见：新增按钮 -->
      <el-button v-if="userRole === 1" type="primary" icon="Plus" @click="handleCreate">我要报修</el-button>
      
      <!-- 维修工/管理员可见：只看待处理的开关 -->
      <el-checkbox v-if="userRole !== 1" v-model="showOnlyPending" label="只看待处理" @change="fetchData" style="margin-left: 20px;"/>
      
      <el-button type="primary" icon="Refresh" @click="fetchData" style="margin-left: 10px;">刷新列表</el-button>
    </div>

    <el-table :data="tableData" border stripe style="width: 100%">
      <el-table-column prop="id" label="单号" width="80" />
      <el-table-column prop="title" label="标题" width="150" />
      <el-table-column prop="description" label="描述" />
      
      <el-table-column label="位置" width="120">
        <template #default="scope">
           <!-- 这里的字段名要看你后端返回的实体类结构，假设后端做了联表查询 -->
           {{ scope.row.building_name }} {{ scope.row.room_number }}
        </template>
      </el-table-column>

      <el-table-column prop="repairman_name" label="维修师傅" width="120">
        <template #default="scope">
          {{ scope.row.repairman_name || '未指派' }}
        </template>
      </el-table-column>

      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="statusMap[scope.row.status].type">
            {{ statusMap[scope.row.status].label }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          
          <!-- 学生操作: 仅待处理时可撤销 -->
          <el-button v-if="userRole === 1 && scope.row.status === 0" 
                     size="small" type="danger" @click="handleDelete(scope.row)">撤销</el-button>

          <!-- 维修工操作: 抢单 / 完成 -->
          <template v-if="userRole === 2">
            <el-button v-if="scope.row.status === 0" 
                       size="small" type="success" @click="handleTakeOrder(scope.row)">接单</el-button>
            
            <el-button v-if="scope.row.status === 1 && isMyTask(scope.row)" 
                       size="small" type="primary" @click="handleFinish(scope.row)">维修完成</el-button>
          </template>

          <!-- 管理员操作: 强制指派(这里简化为管理员可以直接点完成或者删除) -->
           <el-button v-if="userRole === 0" 
                     size="small" type="danger" link @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 报修弹窗代码同上一次，省略... -->
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 假设当前登录用户 (从 localStorage 获取)
// role: 0-管理员, 1-学生, 2-维修工
// id: 当前用户ID (比如维修工ID是 3)
const currentUser = JSON.parse(localStorage.getItem('user')) || { role: 2, id: 3, username: 'worker01' }
const userRole = currentUser.role 

const showOnlyPending = ref(false)
const tableData = ref([])

const statusMap = {
  0: { label: '待接单', type: 'danger' },
  1: { label: '维修中', type: 'warning' },
  2: { label: '已完成', type: 'success' }
}

// 判断这个单子是不是当前维修工接的
const isMyTask = (row) => {
  return row.repairman_id === currentUser.id
}

const fetchData = () => {
  // 模拟从后端获取的数据
  // 实际开发中：根据 role 传参。
  // 如果是学生：后端只返回 user_id = current.id 的数据
  // 如果是维修工/管理员：返回所有数据
  
  const mockData = [
    { 
      id: 1, title: '厕所灯坏了', description: '闪烁', status: 0, 
      building_name: 'A栋', room_number: '101', repairman_id: null, repairman_name: null 
    },
    { 
      id: 2, title: '门锁卡住', description: '钥匙插不进去', status: 1, 
      building_name: 'A栋', room_number: '102', repairman_id: 3, repairman_name: '李师傅' 
    }
  ]
  
  // 简单模拟前端过滤
  if (showOnlyPending.value) {
    tableData.value = mockData.filter(item => item.status === 0)
  } else {
    tableData.value = mockData
  }
}

// 维修工接单
const handleTakeOrder = (row) => {
  ElMessageBox.confirm('确定要接下这个维修单吗？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消' })
    .then(() => {
      // 1. 调用后端接口: POST /api/repair/take { repairId: row.id, repairmanId: currentUser.id }
      // 2. 成功后更新本地数据状态
      row.status = 1
      row.repairman_id = currentUser.id
      row.repairman_name = currentUser.real_name || currentUser.username
      ElMessage.success('接单成功，请尽快前往维修')
    })
}

// 维修工完成
const handleFinish = (row) => {
  ElMessageBox.confirm('确认已维修完成？', '提示')
    .then(() => {
      // 调用后端接口: POST /api/repair/finish { id: row.id }
      row.status = 2
      ElMessage.success('订单已完成')
    })
}

// 删除/撤销
const handleDelete = (row) => {
  ElMessageBox.confirm('确定删除/撤销吗？').then(() => {
     ElMessage.success('操作成功')
     // 刷新列表...
  })
}

onMounted(() => {
  fetchData()
})
</script>