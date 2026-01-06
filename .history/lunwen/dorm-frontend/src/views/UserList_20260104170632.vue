<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" style="display: flex; justify-content: space-between; align-items: center;">
        <!-- <span style="font-weight: bold; font-size: 16px;">人员信息管理</span> -->
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
        <el-table-column prop="username" label="账号/工号" width="150" align="center"/>
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
              {{ row.buildingName ? row.zoneName + ' ' + row.buildingName + ' ' + row.roomNumber : '未分配宿舍' }}
              <span v-if="row.bedNum"> ({{ row.bedNum }}号床)</span>
            </div>
            <div v-else style="color: #ccc;">-</div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
             <el-button type="primary" size="small" icon="Edit" @click="handleEdit(row)">编辑</el-button>
             <el-button type="danger" size="small" icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 20px; text-align: right;">
        <el-pagination 
          background 
          layout="total, prev, pager, next" 
          :total="total" 
          :page-size="pageSize" 
          :current-page="currentPage"
          @current-change="handleCurrentChange" 
        />
      </div>

      <!-- 添加/编辑人员弹窗 -->
      <el-dialog v-model="dialogVisible" :title="isEditMode ? '编辑用户' : '添加新用户'" width="600px">
        <el-form :model="form" label-width="80px">
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

          <!-- 宿舍选择区域 (仅学生显示) -->
          <template v-if="form.role === 1">
            <el-divider content-position="left">住宿信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="宿舍区">
                  <!-- 改为下拉框 -->
                  <el-select v-model="form.zoneName" placeholder="请选择园区" style="width: 100%">
                    <el-option label="明德园" value="明德园" />
                    <el-option label="求是园" value="求是园" />
                    <el-option label="砺尖园" value="砺尖园" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="楼栋">
                  <!-- 改为下拉框，提供 1-20号楼 -->
                  <el-select v-model="form.buildingName" placeholder="请选择楼栋" filterable allow-create style="width: 100%">
                    <el-option v-for="i in 20" :key="i" :label="i + '号楼'" :value="i + '号楼'" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="寝室号">
                  <!-- 自动生成 101-510 的选项 -->
                  <el-select v-model="form.roomNumber" placeholder="选择寝室" filterable style="width: 100%">
                    <el-option v-for="room in roomOptions" :key="room" :label="room" :value="room" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="床位号">
                  <!-- 固定 1-4 号床 -->
                  <el-select v-model="form.bedNum" placeholder="选择床位" style="width: 100%" clearable>
                    <el-option v-for="i in 4" :key="i" :label="i + '号床'" :value="i" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider content-position="left">学籍信息</el-divider>
            <el-form-item label="学院"><el-input v-model="form.college" placeholder="例如：计算机学院" /></el-form-item>
            <el-form-item label="专业"><el-input v-model="form.major" placeholder="例如：软件工程" /></el-form-item>
            <el-form-item label="班级"><el-input v-model="form.className" placeholder="例如：2201班" /></el-form-item>
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
import { ref, reactive, onMounted, computed } from 'vue' // 引入 computed
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)
const filterRole = ref('')
const dialogVisible = ref(false)
const isEditMode = ref(false)

const form = reactive({
  id: null, 
  username: '', realName: '', role: 1, phone: '', 
  college: '', major: '', className: '', 
  zoneName: '', buildingName: '', roomNumber: '', bedNum: ''
})

// 计算属性：生成寝室号选项 (5层，每层10间)
const roomOptions = computed(() => {
  const rooms = []
  for (let floor = 1; floor <= 5; floor++) {
    for (let room = 1; room <= 10; room++) {
      // 格式化为 101, 102 ... 110
      const roomNum = `${floor}${room < 10 ? '0' + room : room}`
      rooms.push(roomNum)
    }
  }
  return rooms
})

const fetchData = () => {
  axios.get('http://192.168.12.26:8080/api/user/list', {
    params: { pageNum: currentPage.value, pageSize: pageSize.value, role: filterRole.value === '' ? null : filterRole.value }
  }).then(res => {
    if (res.data.code === 200) {
      tableData.value = res.data.data.list
      total.value = res.data.data.total
    }
  }).catch(err => {
    console.error("获取用户列表失败:", err);
    ElMessage.error("加载数据失败");
  });
}

const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const handleAdd = () => {
  isEditMode.value = false;
  Object.keys(form).forEach(key => form[key] = '');
  form.role = 1;
  dialogVisible.value = true;
}

const handleEdit = (row) => {
  isEditMode.value = true;
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

const submitForm = () => {
  if(!form.username || !form.realName) return ElMessage.warning('请填写账号和姓名')
  if (form.role === 1) {
    if (!form.zoneName || !form.buildingName || !form.roomNumber) {
        ElMessage.warning('请选择完整的宿舍信息')
        // return; // 可选：是否强制填写
    }
    // 确保 bedNum 是数字或 null
    form.bedNum = (form.bedNum === '' || form.bedNum === null) ? null : Number(form.bedNum); 
  }
  
  const url = isEditMode.value ? 'http://192.168.12.26:8080/api/user/update' : 'http://192.168.12.26:8080/api/user/add';
  
  axios.post(url, form).then(res => {
    if(res.data.code === 200) {
      ElMessage.success(isEditMode.value ? '修改成功' : '添加成功');
      dialogVisible.value = false;
      fetchData();
    } else {
      ElMessage.error(res.data.msg);
    }
  }).catch(err => {
    console.error("提交失败:", err);
    ElMessage.error("提交失败");
  });
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除用户 ${row.realName} (账号: ${row.username}) 吗？`, '警告', { type: 'warning' }).then(() => {
    axios.post('http://192.168.12.26:8080/api/user/delete', { id: row.id }).then(res => {
      if (res.data.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      } else {
        ElMessage.error(res.data.msg)
      }
    })
  })
}

onMounted(() => { fetchData() })
</script>

<style scoped>
.app-container { padding: 0; background-color: transparent; }
.box-card { min-height: calc(100vh - 100px); border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
</style>