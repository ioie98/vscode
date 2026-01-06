<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" style="display: flex; justify-content: space-between; align-items: center;">
        <!-- <span style="font-weight: bold; font-size: 16px;">人员信息管理</span> -->
        <el-button type="primary" icon="Plus" @click="handleAdd">添加人员</el-button>
      </div>

      <div style="margin: 20px 0;">
        <el-radio-group v-model="filterRole" @change="fetchData">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button :label="1">学生</el-radio-button>
          <el-radio-button :label="2">维修工</el-radio-button>
          <el-radio-button :label="0">管理员</el-radio-button>
        </el-radio-group>
      </div>

      <el-table :data="tableData" border stripe style="width: 100%" :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }">
        <el-table-column prop="username" label="账号/工号" width="150" />
        <el-table-column prop="realName" label="姓名" width="120" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.role === 0" type="danger" size="small">管理员</el-tag>
            <el-tag v-else-if="row.role === 1" size="small">学生</el-tag>
            <el-tag v-else type="warning" size="small">维修工</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系电话" width="150" />
        <el-table-column label="宿舍/班级信息" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="row.role === 1">
              <el-tag size="small" type="info" v-if="row.college">{{ row.college }}</el-tag> 
              {{ row.buildingName ? row.zoneName + row.buildingName + '-' + row.roomNumber : '未分配宿舍' }}
              <span v-if="row.bedNum"> (床位: {{ row.bedNum }})</span>
            </div>
            <div v-else style="color: #ccc;">-</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
             <!-- 新增：编辑按钮 -->
             <el-button type="primary" size="small" icon="Edit" @click="handleEdit(row)">编辑</el-button>
             <el-button type="danger" size="small" icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 20px; text-align: right;">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="pageSize" :current-page="currentPage" @current-change="handleCurrentChange" />
      </div>

      <!-- 添加/编辑人员弹窗 -->
      <el-dialog v-model="dialogVisible" :title="isEditMode ? '编辑用户' : '添加新用户'" width="500px">
        <el-form :model="form" label-width="80px">
          <!-- 编辑模式下不允许修改角色和账号，防止逻辑混乱 -->
          <el-form-item label="角色">
            <el-radio-group v-model="form.role" :disabled="isEditMode">
              <el-radio :label="1">学生</el-radio>
              <el-radio :label="2">维修工</el-radio>
              <el-radio :label="0">管理员</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="账号">
            <el-input v-model="form.username" placeholder="学号 或 工号" :disabled="isEditMode" />
          </el-form-item>
          <el-form-item label="姓名"><el-input v-model="form.realName" placeholder="真实姓名" /></el-form-item>
          <el-form-item label="电话"><el-input v-model="form.phone" placeholder="联系方式" /></el-form-item>
          
          <template v-if="form.role === 1">
            <el-divider content-position="left">住宿信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="12"><el-form-item label="宿舍区"><el-input v-model="form.zoneName" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="楼栋"><el-input v-model="form.buildingName" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12"><el-form-item label="寝室号"><el-input v-model="form.roomNumber" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="床位号"><el-input v-model="form.bedNum" type="number" /></el-form-item></el-col>
            </el-row>
            <el-divider content-position="left">学籍信息</el-divider>
            <el-form-item label="学院"><el-input v-model="form.college" /></el-form-item>
            <el-form-item label="专业"><el-input v-model="form.major" /></el-form-item>
            <el-form-item label="班级"><el-input v-model="form.className" /></el-form-item>
          </template>
          
          <div v-if="!isEditMode" style="text-align: right; color: #999; font-size: 12px;">默认密码: 123456</div>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)
const filterRole = ref('')
const dialogVisible = ref(false)
const isEditMode = ref(false) // 新增：是否为编辑模式

const form = reactive({
  id: null, // 新增：编辑时需要ID
  username: '', realName: '', role: 1, phone: '', college: '', major: '', className: '', zoneName: '', buildingName: '', roomNumber: '', bedNum: ''
})

const fetchData = () => {
  axios.get('http://192.168.12.26:8080/api/user/list', {
    params: { pageNum: currentPage.value, pageSize: pageSize.value, role: filterRole.value === '' ? null : filterRole.value }
  }).then(res => {
    if (res.data.code === 200) {
      tableData.value = res.data.data.list
      total.value = res.data.data.total
    }
  })
}

const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const handleAdd = () => {
  isEditMode.value = false;
  Object.keys(form).forEach(key => form[key] = '');
  form.role = 1;
  dialogVisible.value = true;
}

// 新增：点击编辑按钮
const handleEdit = (row) => {
  isEditMode.value = true;
  // 回显数据
  form.id = row.id;
  form.username = row.username;
  form.realName = row.realName;
  form.role = row.role;
  form.phone = row.phone;
  form.college = row.college;
  form.major = row.major;
  form.className = row.className;
  form.zoneName = row.zoneName;
  form.buildingName = row.buildingName;
  form.roomNumber = row.roomNumber;
  form.bedNum = row.bedNum;
  
  dialogVisible.value = true;
}

// 修改：统一提交函数
const submitForm = () => {
  if(!form.username || !form.realName) return ElMessage.warning('请填写账号和姓名')
  if (form.role === 1) form.bedNum = form.bedNum ? Number(form.bedNum) : null; 
  
  // 判断是新增还是更新
  const url = isEditMode.value ? 'http://192.168.12.26:8080/api/user/update' : 'http://192.168.12.26:8080/api/user/add';
  
  axios.post(url, form).then(res => {
    if(res.data.code === 200) {
      ElMessage.success(isEditMode.value ? '修改成功' : '添加成功');
      dialogVisible.value = false;
      fetchData();
    } else {
      ElMessage.error(res.data.msg);
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除?`, '警告').then(() => {
    axios.post('http://192.168.12.26:8080/api/user/delete', { id: row.id }).then(res => {
      ElMessage.success('删除成功'); fetchData()
    })
  })
}

onMounted(() => { fetchData() })
</script>

<style scoped> .app-container { padding: 0; background-color: transparent; } .box-card { min-height: calc(100vh - 100px); border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); } </style>