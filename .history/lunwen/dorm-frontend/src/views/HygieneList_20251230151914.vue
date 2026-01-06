<template>
  <el-card>
    <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
      <span style="font-weight: bold;">卫生检查记录</span>
      <div class="header-actions">
        <el-tag v-if="user.role === 0" style="margin-right: 10px;">全校视图</el-tag>
        <!-- 新增：管理员才能看到新增按钮 -->
        <el-button v-if="user.role === 0" type="primary" icon="Plus" @click="openAddDialog">新增检查</el-button>
      </div>
    </div>
    
    <el-table :data="tableData" stripe style="width: 100%; margin-top: 20px;">
      <!-- 宿舍列 (管理员看的时候很有用，学生看自己宿舍时显示“本宿舍”) -->
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
      
      <el-table-column prop="score" label="得分" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.score >= 90 ? 'success' : 'warning'">
            {{ scope.row.score }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="remark" label="检查情况 / 备注" />
    </el-table>

    <div v-if="tableData.length === 0" style="text-align: center; color: #999; margin-top: 20px;">
      暂无检查记录
    </div>

    <!-- 新增：管理员新增检查的弹窗 -->
    <el-dialog v-model="addDialogVisible" title="新增卫生检查记录" width="500px">
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="宿舍">
          <el-select v-model="addForm.dormId" placeholder="请选择宿舍" style="width: 100%;">
            <el-option
              v-for="dorm in dormList"
              :key="dorm.id"
              :label="dorm.zoneName + dorm.buildingName + '-' + dorm.roomNumber"
              :value="dorm.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="得分">
          <el-input-number v-model="addForm.score" :min="0" :max="100" controls-position="right" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="检查日期">
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
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const tableData = ref([])
const user = JSON.parse(localStorage.getItem('user') || '{}')

// 弹窗相关
const addDialogVisible = ref(false)
const addForm = reactive({
  dormId: null,
  score: 100, // 默认100分
  checkDate: new Date(), // 默认今天
  remark: ''
})
const dormList = ref([]) // 存储所有宿舍列表，供管理员选择

const fetchData = () => {
  if (user.role === 1 && !user.dormId) return
  
  axios.get(`http://localhost:8080/api/common/hygiene/list`, {
    params: {
      dormId: user.dormId,
      role: user.role
    }
  }).then(res => {
      if (res.data.code === 200) {
        tableData.value = res.data.data
      }
    })
}

// 获取所有宿舍列表
const fetchDormList = () => {
  axios.get('http://localhost:8080/api/dorm/list').then(res => { // 需要一个获取宿舍列表的接口
    if (res.data.code === 200) {
      dormList.value = res.data.data
    }
  })
}

// 打开新增弹窗
const openAddDialog = () => {
  addForm.dormId = null;
  addForm.score = 100;
  addForm.checkDate = new Date();
  addForm.remark = '';
  addDialogVisible.value = true;
  fetchDormList(); // 打开弹窗时获取宿舍列表
}

// 提交新增表单
const submitAddForm = () => {
  if (!addForm.dormId || !addForm.score || !addForm.checkDate) {
    ElMessage.warning('请填写完整的宿舍、得分和检查日期');
    return;
  }
  
  axios.post('http://localhost:8080/api/common/hygiene/add', addForm).then(res => {
    if (res.data.code === 200) {
      ElMessage.success('添加成功');
      addDialogVisible.value = false;
      fetchData(); // 刷新列表
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