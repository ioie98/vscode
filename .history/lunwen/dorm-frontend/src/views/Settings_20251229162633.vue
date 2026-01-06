<template>
  <el-card>
    <el-tabs>
      <el-tab-pane label="修改密码">
        <el-form :model="form" label-width="100px" style="max-width: 500px; margin-top: 20px;">
          <el-form-item label="旧密码">
            <el-input v-model="form.oldPwd" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="form.newPwd" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input v-model="form.confirmPwd" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="success" @click="save">确认修改</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = reactive({ oldPwd: '', newPwd: '', confirmPwd: '' })
const user = JSON.parse(localStorage.getItem('user'))

const save = () => {
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
  })
}
</script>