<template>
  <div class="login-container">
    <div class="bg-gradient"></div> 

    <el-card class="login-card">
      <h2 class="title">高校宿舍管理系统</h2>
      <el-form :model="form" :rules="rules" ref="loginFormRef" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号/学号" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="tips">
        <p>测试账号: admin / 20220801 / linshu</p>
        <p>默认密码: 123456</p>
      </div>
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
      
      axios.post('http://localhost:8080/api/login', form)
        .then(res => {
          const result = res.data 
          
          if (result.code === 200) {
            ElMessage.success('登录成功')
            localStorage.setItem('user', JSON.stringify(result.data))
            router.push('/my-dorm') // 登录成功后跳转到我的宿舍
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
  position: relative;
  overflow: hidden; 
}

.bg-gradient {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #74ebd5 0%, #9face6 100%); 
  animation: bgAnimation 15s ease infinite; 
  background-size: 200% 200%;
}

@keyframes bgAnimation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.login-card {
  width: 400px;
  padding: 40px; 
  border-radius: 12px; 
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2); 
  background: rgba(255, 255, 255, 0.95); 
  backdrop-filter: blur(5px); 
  position: relative; 
  z-index: 10;
}
.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 28px; 
  font-weight: bold;
  letter-spacing: 1px; 
}
.tips {
  margin-top: 25px;
  font-size: 13px;
  color: #777;
  text-align: center;
  line-height: 1.6;
}

.el-input__wrapper.is-focus, .el-input__wrapper:hover {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset !important;
}
.el-button--primary:focus, .el-button--primary:hover {
  background-color: var(--el-color-primary-light-1);
}
</style>