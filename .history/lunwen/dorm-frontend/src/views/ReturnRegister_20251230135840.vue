<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">学生返校登记</span>
        <el-button icon="Refresh" circle @click="resetForm" style="margin-left: 10px;" />
      </div>

      <el-form :model="form" label-width="120px" style="max-width: 600px; margin-top: 20px;">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" disabled />
        </el-form-item>
        <el-form-item label="学号" prop="studentId">
          <el-input v-model="form.studentId" disabled />
        </el-form-item>
        
        <el-form-item label="返校时间" prop="returnTime">
          <el-date-picker v-model="form.returnTime" type="date" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
        
        <el-form-item label="是否延迟" prop="isDelayed">
          <el-radio-group v-model="form.isDelayed">
            <el-radio label="否">按时返校</el-radio>
            <el-radio label="是">延迟返校</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="延迟原因" v-if="form.isDelayed === '是'" prop="reason">
          <el-input v-model="form.reason" type="textarea" placeholder="请输入延迟原因" />
        </el-form-item>
        
        <el-form-item label="交通方式" prop="transport">
          <el-select v-model="form.transport" placeholder="请选择" style="width: 100%">
            <el-option label="高铁/火车" value="高铁/火车" />
            <el-option label="飞机" value="飞机" />
            <el-option label="长途大巴" value="长途大巴" />
            <el-option label="私家车" value="私家车" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="车次/航班号" prop="transportNo">
          <el-input v-model="form.transportNo" placeholder="如 G1234 或 CA1234" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="submit">提交登记</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')

const form = reactive({
  studentId: user.username,
  name: user.realName || user.username,
  returnTime: '',
  isDelayed: '否',
  reason: '',
  transport: '',
  transportNo: ''
})

const resetForm = () => {
    form.returnTime = '';
    form.isDelayed = '否';
    form.reason = '';
    form.transport = '';
    form.transportNo = '';
    ElMessage.info('表单已重置');
};

const submit = () => {
  if(!form.returnTime || !form.transport) {
    ElMessage.warning('请填写完整信息');
    return;
  }
  if (form.isDelayed === '是' && !form.reason) {
    ElMessage.warning('请填写延迟返校原因');
    return;
  }
  
  axios.post('http://localhost:8080/api/common/return/add', form).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('登记成功')
      router.push('/return') // 提交后跳转到返校管理列表页
    } else {
      ElMessage.error(res.data.msg);
    }
  }).catch(err => {
    console.error("提交返校登记失败:", err);
    ElMessage.error("提交失败，请检查网络或控制台错误");
  });
}

onMounted(() => {
    // 可以在这里检查是否有未完成的登记，并加载
    // 暂时只做表单初始化
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