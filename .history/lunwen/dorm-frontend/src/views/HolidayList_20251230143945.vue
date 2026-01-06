<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <!-- 左侧标题 -->
        <span style="font-weight: bold; font-size: 16px;">节假日去向统计</span>
        
        <!-- 右侧操作区：包含标签、登记按钮、刷新按钮 -->
        <!-- 修改点：使用 flex 布局和 gap 属性来控制内部元素的间距 -->
        <div class="header-actions" style="display: flex; align-items: center; gap: 10px;">
          <el-tag v-if="user.role === 1" type="success">本宿舍</el-tag>
          <el-tag v-if="user.role === 0" type="danger">全校数据</el-tag>
          
          <el-button v-if="user.role === 1" type="primary" icon="Edit" @click="openAddDialog">登记去向</el-button>
          <el-button icon="Refresh" circle @click="fetchData" />
        </div>
      </div>

      <div class="filter-header" style="padding-bottom: 15px; border-bottom: 1px dashed #eee;">
        <span>去向筛选：</span>
        <el-select v-model="query" placeholder="全部" style="width: 150px; margin-right: 10px;" @change="fetchData">
          <el-option label="全部" value="全部" />
          <el-option label="留校" value="留校" />
          <el-option label="回家" value="回家" />
          <el-option label="其他" value="其他" />
        </el-select>
        <el-button type="primary" icon="Search" @click="fetchData">查询</el-button>
      </div>

      <el-table 
        :data="tableData" 
        border 
        stripe 
        style="margin-top: 20px;"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="major" label="专业" width="120" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column prop="destination" label="去向" align="center">
          <template #default="{ row }">
            <el-tag :type="row.destination === '留校' ? 'primary' : 'warning'" size="small">{{ row.destination }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="具体目的地" />
        <el-table-column prop="returnTime" label="回校时间">
          <template #default="{row}">{{ row.returnTime ? row.returnTime.substring(0,10) : '' }}</template>
        </el-table-column>
      </el-table>

      <div v-if="tableData.length === 0" style="text-align: center; color: #999; margin-top: 20px;">
        暂无数据
      </div>

      <!-- 学生登记去向弹窗 -->
      <el-dialog v-model="addDialogVisible" title="登记节假日去向" width="500px">
        <el-form :model="addForm" label-width="100px">
          <el-form-item label="姓名" prop="name">
            <el-input v-model="addForm.name" disabled />
          </el-form-item>
          <el-form-item label="学号" prop="studentId">
            <el-input v-model="addForm.studentId" disabled />
          </el-form-item>
          <el-form-item label="去向" prop="destination">
            <el-radio-group v-model="addForm.destination">
              <el-radio label="留校">留校</el-radio>
              <el-radio label="回家">回家</el-radio>
              <el-radio label="其他">其他</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="目的地" prop="location">
            <el-input v-model="addForm.location" placeholder="例如：学校宿舍 / 杭州市西湖区" />
          </el-form-item>
          <el-form-item label="回校时间" prop="returnTime">
            <el-date-picker v-model="addForm.returnTime" type="date" placeholder="选择回校日期" style="width: 100%;" />
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

const query = ref('全部')
const tableData = ref([])
const user = JSON.parse(localStorage.getItem('user') || '{}')

const addDialogVisible = ref(false)
const addForm = reactive({
  studentId: user.username,
  name: user.realName || user.username,
  major: user.major || '', 
  className: user.className || '', 
  phone: user.phone || '', 
  destination: '留校', 
  location: '',
  returnTime: ''
})

const fetchData = () => {
  axios.get(`http://192.168.12.26:8080/api/common/holiday/list`, { // 使用你的局域网IP
    params: {
      destination: query.value === '全部' ? null : query.value,
      role: user.role,     
      dormId: user.dormId,  
    }
  }).then(res => {
       if(res.data.code === 200) tableData.value = res.data.data
    }).catch(err => {
      console.error("获取节假日去向失败:", err);
      ElMessage.error("加载数据失败，请检查网络或控制台错误");
    });
}

const openAddDialog = () => {
  addForm.destination = '留校';
  addForm.location = '';
  addForm.returnTime = '';
  
  addForm.studentId = user.username;
  addForm.name = user.realName || user.username;
  addForm.major = user.major || '';
  addForm.className = user.className || '';
  addForm.phone = user.phone || '';

  addDialogVisible.value = true;
}

const submitAddForm = () => {
  if (!addForm.destination || !addForm.location || !addForm.returnTime) {
    ElMessage.warning('请填写完整的去向、目的地和回校时间');
    return;
  }
  
  axios.post('http://192.168.12.26:8080/api/common/holiday/add', addForm).then(res => { // 使用你的局域网IP
    if (res.data.code === 200) {
      ElMessage.success('登记成功');
      addDialogVisible.value = false;
      fetchData(); 
    } else {
      ElMessage.error(res.data.msg);
    }
  }).catch(err => {
    console.error("提交节假日去向失败:", err);
    ElMessage.error("登记失败，请检查网络或控制台错误");
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
.filter-header { 
  display: flex; 
  align-items: center; 
} 
</style>