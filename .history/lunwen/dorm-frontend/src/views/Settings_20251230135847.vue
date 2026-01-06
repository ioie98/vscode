<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">个人设置</span>
        <el-button icon="Refresh" circle @click="resetForm" style="margin-left: 10px;" />
      </div>

      <el-tabs>
        <el-tab-pane label="修改密码">
          <el-form :model="form" label-width="100px" style="max-width: 500px; margin-top: 20px;">
            <el-form-item label="旧密码" prop="oldPwd">
              <el-input v-model="form.oldPwd" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPwd">
              <el-input v-model="form.newPwd" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPwd">
              <el-input v-model="form.confirmPwd" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="save">确认修改</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = reactive({ oldPwd: '', newPwd: '', confirmPwd: '' })
const user = JSON.parse(localStorage.getItem('user'))

const resetForm = () => {
    form.oldPwd = '';
    form.newPwd = '';
    form.confirmPwd = '';
    ElMessage.info('表单已重置');
};

const save = () => {
  if (!form.oldPwd || !form.newPwd || !form.confirmPwd) {
    ElMessage.warning('请填写所有密码字段');
    return;
  }
  if (form.newPwd !== form.confirmPwd) {
    ElMessage.error('两次输入密码不一致')
    return
  }
  axios.post('http://localhost:8080/api/common/update-password', {
    id: user.id,
    oldPwd: form.oldPwd,
    newPwd: form.newPwd
  }).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('修改成功，请重新登录')
      localStorage.removeItem('user')
      router.push('/login')
    } else {
      ElMessage.error(res.data.msg)
    }
  }).catch(err => {
    console.error("修改密码失败:", err);
    ElMessage.error("修改失败，请检查网络或控制台错误");
  });
}
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