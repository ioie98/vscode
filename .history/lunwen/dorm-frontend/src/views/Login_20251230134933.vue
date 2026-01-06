<template>
  <div class="login-container">
    <!-- 增加渐变背景，可以是动态或静态图片 -->
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
      
      // 发送请求给 Spring Boot 后端
      axios.post('http://localhost:8080/api/login', form)
        .then(res => {
          // 注意：这里要看后端返回的数据结构，通常 axios 包了一层 data
          // 你的后端返回格式是: { code: 200, msg: "...", data: {...} }
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
  position: relative;
  overflow: hidden; /* 隐藏超出容器的背景 */
}

/* 渐变背景层 */
.bg-gradient {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #74ebd5 0%, #9face6 100%); /* 清爽的蓝绿色渐变 */
  animation: bgAnimation 15s ease infinite; /* 增加一个缓慢的动画 */
  background-size: 200% 200%;
}

@keyframes bgAnimation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.login-card {
  width: 400px;
  padding: 40px; /* 增加内边距 */
  border-radius: 12px; /* 更圆润的边角 */
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2); /* 更明显的阴影效果 */
  background: rgba(255, 255, 255, 0.95); /* 半透明背景，能看到一点背景渐变 */
  backdrop-filter: blur(5px); /* 毛玻璃效果 (现代浏览器支持) */
  position: relative; /* 确保卡片在背景之上 */
  z-index: 10;
}
.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 28px; /* 标题更大 */
  font-weight: bold;
  letter-spacing: 1px; /* 字符间距 */
}
.tips {
  margin-top: 25px;
  font-size: 13px;
  color: #777;
  text-align: center;
  line-height: 1.6;
}

/* 优化输入框和按钮的焦点样式 (可选) */
.el-input__wrapper.is-focus, .el-input__wrapper:hover {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset !important;
}
.el-button--primary:focus, .el-button--primary:hover {
  background-color: var(--el-color-primary-light-1);
}
</style>