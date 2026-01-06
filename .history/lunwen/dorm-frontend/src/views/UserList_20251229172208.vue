<template>
  <el-card>
    <div slot="header" style="display: flex; justify-content: space-between; align-items: center;">
      <span style="font-weight: bold; font-size: 16px;">人员信息管理</span>
      <el-button type="primary" icon="Plus" @click="handleAdd">添加人员</el-button>
    </div>

    <!-- 筛选栏 -->
    <div style="margin: 20px 0;">
      <el-radio-group v-model="filterRole" @change="fetchData">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button :label="1">学生</el-radio-button>
        <el-radio-button :label="2">维修工</el-radio-button>
        <el-radio-button :label="0">管理员</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 表格 -->
    <el-table :data="tableData" border stripe style="width: 100%">
      <el-table-column prop="username" label="账号/工号" width="150" />
      <el-table-column prop="realName" label="姓名" width="120" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.role === 0" type="danger">管理员</el-tag>
          <el-tag v-else-if="row.role === 1">学生</el-tag>
          <el-tag v-else type="warning">维修工</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="联系电话" width="150" />
      
      <!-- 学生特有信息 -->
      <el-table-column label="宿舍/班级信息" min-width="200">
        <template #default="{ row }">
          <div v-if="row.role === 1">
            <el-tag size="small" type="info">{{ row.college }}</el-tag> 
            {{ row.buildingName ? row.buildingName + '-' + row.roomNumber : '未分配宿舍' }}
          </div>
          <div v-else style="color: #ccc;">-</div>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
           <el-button type="danger" size="small" icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增弹窗 -->
    <el-dialog v-model="dialogVisible" title="添加新用户" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="角色">
          <el-radio-group v-model="form.role">
            <el-radio :label="1">学生</el-radio>
            <el-radio :label="2">维修工</el-radio>
            <el-radio :label="0">管理员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="账号">
          <el-input v-model="form.username" placeholder="学号 或 工号" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.realName" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" placeholder="联系方式" />
        </el-form-item>

        <!-- 只有选学生时才显示 -->
        <template v-if="form.role === 1">
          <el-form-item label="学院">
            <el-input v-model="form.college" />
          </el-form-item>
          <el-form-item label="专业">
            <el-input v-model="form.major" />
          </el-form-item>
          <el-form-item label="班级">
            <el-input v-model="form.className" />
          </el-form-item>
        </template>
        
        <div style="text-align: right; color: #999; font-size: 12px;">默认密码: 123456</div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAdd">确定添加</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const allData = ref([]) // 存所有数据，用于前端筛选
const filterRole = ref('') // 筛选器
const dialogVisible = ref(false)

const form = reactive({
  username: '', realName: '', role: 1, phone: '', college: '', major: '', className: ''
})

const fetchData = () => {
  axios.get('http://localhost:8080/api/user/list').then(res => {
    if (res.data.code === 200) {
      allData.value = res.data.data
      applyFilter()
    }
  })
}

// 前端过滤逻辑
const applyFilter = () => {
  if (filterRole.value === '') {
    tableData.value = allData.value
  } else {
    tableData.value = allData.value.filter(item => item.role === filterRole.value)
  }
}

const handleAdd = () => {
  // 重置表单
  form.username = ''
  form.realName = ''
  form.role = 2 // 默认添加维修工
  form.phone = ''
  dialogVisible.value = true
}

const submitAdd = () => {
  if(!form.username || !form.realName) return ElMessage.warning('请填写完整')
  
  axios.post('http://localhost:8080/api/user/add', form).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('添加成功')
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(res.data.msg)
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除用户 ${row.realName} 吗？`, '警告', { type: 'warning' }).then(() => {
    axios.post('http://localhost:8080/api/user/delete', { id: row.id }).then(res => {
      ElMessage.success('删除成功')
      fetchData()
    })
  })
}

onMounted(() => {
  fetchData()
})
</script>