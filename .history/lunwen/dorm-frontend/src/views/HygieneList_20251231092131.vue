<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <!-- <span style="font-weight: bold; font-size: 16px;">卫生检查记录</span> -->
        <div class="header-actions">
          <el-tag v-if="user.role === 0" style="margin-right: 10px;">全校视图</el-tag>
          <el-button v-if="user.role === 0" type="primary" icon="Plus" size="large" @click="openAddDialog">新增检查</el-button>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px;" />
        </div>
      </div>
      
      <el-table 
        :data="tableData" 
        stripe 
        border 
        v-loading="loading"
        style="width: 100%; margin-top: 10px;" 
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
        <el-table-column label="宿舍" width="150">
          <template #default="{ row }">
            <span v-if="row.buildingName">
              {{ row.buildingName }} {{ row.roomNumber }}
            </span>
            <span v-else>本宿舍</span>
          </template>
        </el-table-column>

        <el-table-column prop="checkDate" label="检查日期" width="180">
          <template #default="scope">
            {{ scope.row.checkDate ? scope.row.checkDate.substring(0, 10) : '' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="score" label="得分" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.score >= 90 ? 'success' : 'warning'" size="small">
              {{ scope.row.score }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="remark" label="检查情况 / 备注" />
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

      <!-- 新增弹窗 -->
      <el-dialog v-model="addDialogVisible" title="新增卫生检查记录" width="500px">
        <el-form :model="addForm" label-width="100px">
          <el-form-item label="宿舍" prop="dormId">
            <el-select v-model="addForm.dormId" placeholder="请选择宿舍" style="width: 100%;">
              <el-option
                v-for="dorm in dormList"
                :key="dorm.id"
                :label="dorm.zoneName + dorm.buildingName + '-' + dorm.roomNumber"
                :value="dorm.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="得分" prop="score">
            <el-input-number v-model="addForm.score" :min="0" :max="100" controls-position="right" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="检查日期" prop="checkDate">
            <el-date-picker v-model="addForm.checkDate" type="date" placeholder="选择日期" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="addForm.remark" type="textarea" :rows="3" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAddForm">提交</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const tableData = ref([])
const loading = ref(false)
const user = JSON.parse(localStorage.getItem('user') || '{}')

// 分页变量
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)

const addDialogVisible = ref(false)
const addForm = reactive({
  dormId: null,
  score: 100, 
  checkDate: new Date(), 
  remark: ''
})
const dormList = ref([])

const fetchData = () => {
  if (user.role === 1 && !user.dormId) {
    tableData.value = []; 
    return;
  }
  loading.value = true
  axios.get(`http://localhost:8080/api/common/hygiene/list`, {
    params: {
      dormId: user.dormId,
      role: user.role,
      pageNum: currentPage.value,
      pageSize: pageSize.value
    }
  }).then(res => {
      if (res.data.code === 200) {
        tableData.value = res.data.data.list
        total.value = res.data.data.total
      }
    }).finally(() => loading.value = false)
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

const fetchDormList = () => {
  axios.get('http://localhost:8080/api/dorm/list').then(res => {
    if (res.data.code === 200) {
      dormList.value = res.data.data
    }
  })
}

const openAddDialog = () => {
  addForm.dormId = null;
  addForm.score = 100;
  addForm.checkDate = new Date();
  addForm.remark = '';
  addDialogVisible.value = true;
  fetchDormList(); 
}

const submitAddForm = () => {
  if (!addForm.dormId || addForm.score === null || !addForm.checkDate) {
    ElMessage.warning('请填写完整的宿舍、得分和检查日期');
    return;
  }
  
  axios.post('http://localhost:8080/api/common/hygiene/add', addForm).then(res => {
    if (res.data.code === 200) {
      ElMessage.success('添加成功');
      addDialogVisible.value = false;
      fetchData(); 
    } else {
      ElMessage.error(res.data.msg);
    }
  }).catch(err => {
    console.error("新增卫生检查失败:", err);
    ElMessage.error("添加失败，请检查网络或控制台错误");
  });
}

onMounted(() => {
  fetchData();
  if (user.role === 0) { 
      fetchDormList();
  }
})
</script>

<style scoped>
.app-container { padding: 0; background-color: transparent; }
.box-card { min-height: calc(100vh - 100px); border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.el-card__header { border-bottom: 1px solid #ebeef5; padding: 18px 20px; }
</style>