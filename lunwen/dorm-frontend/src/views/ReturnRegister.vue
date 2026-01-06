<template>
  <el-card>
    <div slot="header">
      <!-- <span style="font-weight: bold;">学生返校登记</span> -->
    </div>

    <el-form :model="form" label-width="120px" style="max-width: 600px; margin-top: 20px;">
      <el-form-item label="姓名">
        <el-input v-model="form.name" disabled />
      </el-form-item>
      <el-form-item label="学号">
        <el-input v-model="form.studentId" disabled />
      </el-form-item>
      
      <el-form-item label="返校时间">
        <el-date-picker v-model="form.returnTime" type="date" placeholder="选择日期" style="width: 100%" />
      </el-form-item>
      
      <el-form-item label="是否延迟">
        <el-radio-group v-model="form.isDelayed">
          <el-radio label="否">按时返校</el-radio>
          <el-radio label="是">延迟返校</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="延迟原因" v-if="form.isDelayed === '是'">
        <el-input v-model="form.reason" type="textarea" placeholder="请输入原因" />
      </el-form-item>
      
      <el-form-item label="交通方式">
        <el-select v-model="form.transport" placeholder="请选择" style="width: 100%">
          <el-option label="高铁/火车" value="高铁/火车" />
          <el-option label="飞机" value="飞机" />
          <el-option label="长途大巴" value="长途大巴" />
          <el-option label="私家车" value="私家车" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="车次/航班号">
        <el-input v-model="form.transportNo" placeholder="如 G1234" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submit">提交登记</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive } from 'vue'
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

const submit = () => {
  if(!form.returnTime || !form.transport) return ElMessage.warning('请填写完整信息')
  
  axios.post('http://localhost:8080/api/common/return/add', form).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('登记成功')
      // 提交后跳转到列表页查看
      router.push('/return')
    }
  })
}
</script>