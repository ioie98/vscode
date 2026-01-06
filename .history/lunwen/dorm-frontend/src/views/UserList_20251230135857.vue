<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">人员信息管理</span>
        <div class="header-actions">
          <el-button type="primary" icon="Plus" @click="handleAdd">添加人员</el-button>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px;" />
        </div>
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
      <el-table 
        :data="tableData" 
        border 
        stripe 
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
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
        
        <!-- 学生特有信息 -->
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

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 添加人员弹窗 -->
      <el-dialog v-model="dialogVisible" title="添加新用户" width="500px">
        <el-form :model="form" label-width="80px">
          <el-form-item label="角色" prop="role">
            <el-radio-group v-model="form.role">
              <el-radio :label="1">学生</el-radio>
              <el-radio :label="2">维修工</el-radio>
              <el-radio :label="0">管理员</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" placeholder="学号 或 工号" />
          </el-form-item>
          <el-form-item label="姓名" prop="realName">
            <el-input v-model="form.realName" placeholder="真实姓名" />
          </el-form-item>
          <el-form-item label="电话" prop="phone">
            <el-input v-model="form.phone" placeholder="联系方式" />
          </el-form-item>

          <template v-if="form.role === 1">
            <el-divider content-position="left">住宿信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="宿舍区" prop="zoneName">
                  <el-input v-model="form.zoneName" placeholder="例如：求是园" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="楼栋" prop="buildingName">
                  <el-input v-model="form.buildingName" placeholder="例如：8号楼" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="寝室号" prop="roomNumber">
                  <el-input v-model="form.roomNumber" placeholder="例如：101" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="床位号" prop="bedNum">
                  <el-input v-model="form.bedNum" placeholder="1-4 (可空)" type="number" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider content-position="left">学籍信息</el-divider>
            <el-form-item label="学院" prop="college">
              <el-input v-model="form.college" />
            </el-form-item>
            <el-form-item label="专业" prop="major">
              <el-input v-model="form.major" />
            </el-form-item>
            <el-form-item label="班级" prop="className">
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const allData = ref([])
const filterRole = ref('')
const dialogVisible = ref(false)

const form = reactive({
  username: '', 
  realName: '', 
  role: 1, 
  phone: '', 
  college: '', 
  major: '', 
  className: '',
  zoneName: '', 
  buildingName: '', 
  roomNumber: '', 
  bedNum: '' 
})

const fetchData = () => {
  axios.get('http://localhost:8080/api/user/list').then(res => {
    if (res.data.code === 200) {
      allData.value = res.data.data
      applyFilter()
    }
  }).catch(err => {
    console.error("获取用户列表失败:", err);
    ElMessage.error("加载数据失败，请检查网络或控制台错误");
  });
}

const applyFilter = () => {
  if (filterRole.value === '') {
    tableData.value = allData.value
  } else {
    tableData.value = allData.value.filter(item => item.role === filterRole.value)
  }
}

const handleAdd = () => {
  Object.keys(form).forEach(key => {
    form[key] = ''
  })
  form.role = 1; 
  dialogVisible.value = true;
}

const submitAdd = () => {
  if(!form.username || !form.realName) {
    ElMessage.warning('请填写账号和姓名')
    return;
  }
  
  if (form.role === 1) { 
    if (!form.zoneName || !form.buildingName || !form.roomNumber) {
      ElMessage.warning('请填写完整的宿舍区、楼栋和寝室号，否则将无法分配宿舍')
    }
    form.bedNum = form.bedNum ? Number(form.bedNum) : null; 
  }


  axios.post('http://localhost:8080/api/user/add', form).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('添加成功')
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(res.data.msg)
    }
  }).catch(err => {
    console.error("添加用户失败:", err);
    ElMessage.error("添加失败，请检查网络或控制台错误");
  });
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除用户 ${row.realName} (账号: ${row.username}) 吗？`, '警告', { type: 'warning' }).then(() => {
    axios.post('http://localhost:8080/api/user/delete', { id: row.id }).then(res => {
      if (res.data.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      } else {
        ElMessage.error(res.data.msg)
      }
    }).catch(err => {
      console.error("删除用户失败:", err);
      ElMessage.error("删除失败，请检查网络或控制台错误");
    });
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.app-container {
  padding: 0; 
  background-color: transparent; 
}
.box-card {
  min-height: calc(100vh - 100px); 
  border-radius: 8px; 
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); 
}
.clearfix:before, .clearfix:after {
  display: table;
  content: "";
}
.clearfix:after {
  clear: both
}
.el-card__header {
  border-bottom: 1px solid #ebeef5; 
  padding: 18px 20px;
}
</style>