<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="title">高校宿舍管理报修系统</h2>
      <el-form :model="form" :rules="rules" ref="loginFormRef" size="large">
        <el-form-item prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入账号" 
            prefix-icon="User" 
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码" 
            prefix-icon="Lock" 
            show-password 
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = () => {
  loginFormRef.value.validate((valid) => {
    if (valid) {
      loading.value = true
      
      // 发送请求给 Spring Boot 后端
      axios.post('http://localhost:8080/api/login', form)
        .then(res => {
          const result = res.data 
          
          if (result.code === 200) {
            ElMessage.success('登录成功')
            // 1. 存储用户信息到浏览器缓存
            localStorage.setItem('user', JSON.stringify(result.data))
            // 2. 跳转到报修列表页
            router.push('/repair')
          } else {
            ElMessage.error(result.msg || '登录失败')
          }
        })
        .catch(err => {
          console.error(err)
          ElMessage.error('无法连接到后端，请检查后端是否启动 (8080端口)')
        })
        .finally(() => {
          loading.value = false
        })
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #74ebd5 0%, #9face6 100%);
}
.login-card {
  width: 400px;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}
.tips {
  margin-top: 20px;
  font-size: 12px;
  color: #888;
  text-align: center;
  line-height: 1.5;
}
</style>