<template>
  <div class="login-container">
    <div class="bg-gradient"></div>

    <el-card class="login-card">
      <h2 class="title">高校宿舍管理系统</h2>
      
      <!-- 模式切换标题 -->
      <div style="text-align: center; margin-bottom: 20px; font-weight: bold; color: #555;">
        {{ isRegister ? '用户注册' : '用户登录' }}
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" size="large" label-width="0">
        
        <!-- 1. 角色选择 (登录和注册都需要) -->
        <el-form-item prop="role">
          <el-radio-group v-model="form.role" style="width: 100%; justify-content: center;">
            <el-radio :label="1">学生</el-radio>
            <el-radio :label="2">维修工</el-radio>
            <el-radio :label="0">管理员</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 2. 通用字段 -->
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号/学号" prefix-icon="User" />
        </el-form-item>
        
        <!-- 注册时需要输入真实姓名和电话 -->
        <template v-if="isRegister">
          <el-form-item prop="realName">
            <el-input v-model="form.realName" placeholder="请输入真实姓名" prefix-icon="Postcard" />
          </el-form-item>
          <el-form-item prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" prefix-icon="Iphone" />
          </el-form-item>
        </template>

        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
        </el-form-item>

        <!-- 3. 注册且角色为学生时的额外字段 -->
        <template v-if="isRegister && form.role === 1">
          <el-divider content-position="center">宿舍信息</el-divider>
          <el-row :gutter="10">
            <el-col :span="8"><el-input v-model="form.zoneName" placeholder="宿舍区" /></el-col>
            <el-col :span="8"><el-input v-model="form.buildingName" placeholder="楼栋" /></el-col>
            <el-col :span="8"><el-input v-model="form.roomNumber" placeholder="房号" /></el-col>
          </el-row>
          <div style="margin-top: 10px;"></div>
          <el-row :gutter="10">
            <el-col :span="8"><el-input v-model="form.bedNum" placeholder="床位" type="number"/></el-col>
            <el-col :span="16"><el-input v-model="form.college" placeholder="学院" /></el-col>
          </el-row>
          <div style="margin-top: 10px;"></div>
          <el-row :gutter="10">
            <el-col :span="12"><el-input v-model="form.major" placeholder="专业" /></el-col>
            <el-col :span="12"><el-input v-model="form.className" placeholder="班级" /></el-col>
          </el-row>
        </template>

        <!-- 按钮区域 -->
        <el-form-item style="margin-top: 20px;">
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleSubmit">
            {{ isRegister ? '注 册' : '登 录' }}
          </el-button>
        </el-form-item>
        
        <!-- 切换模式 -->
        <div class="toggle-mode">
          <el-link type="primary" @click="toggleMode">
            {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
          </el-link>
        </div>
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
const formRef = ref(null)
const loading = ref(false)
const isRegister = ref(false) // 控制当前是登录还是注册模式

const form = reactive({
  role: 1, // 默认选中学生
  username: '',
  password: '',
  realName: '',
  phone: '',
  zoneName: '',
  buildingName: '',
  roomNumber: '',
  bedNum: '',
  college: '',
  major: '',
  className: ''
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
  // 切换时清空非核心表单
  form.realName = ''
  form.phone = ''
}

const handleSubmit = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      loading.value = true
      
      if (isRegister.value) {
        // === 注册逻辑 ===
        // 注册时 bedNum 需要处理数字转换
        if (form.role === 1) form.bedNum = form.bedNum ? Number(form.bedNum) : null;
        
        axios.post('http://192.168.12.26:8080/api/user/register', form)
          .then(res => {
            if (res.data.code === 200) {
              ElMessage.success('注册成功，请登录')
              isRegister.value = false // 切换回登录
            } else {
              ElMessage.error(res.data.msg)
            }
          })
          .finally(() => loading.value = false)
          
      } else {
        // === 登录逻辑 ===
        axios.post('http://192.168.12.26:8080/api/login', {
          username: form.username,
          password: form.password,
          role: form.role // 传角色给后端校验
        })
        .then(res => {
          if (res.data.code === 200) {
            ElMessage.success('登录成功')
            localStorage.setItem('user', JSON.stringify(res.data.data))
            router.push('/my-dorm')
          } else {
            ElMessage.error(res.data.msg)
          }
        })
        .finally(() => loading.value = false)
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden; 
}

.bg-gradient {
  position: fixed; /* 改为 fixed，背景固定不动，防止滚动条影响 */
  top: 0;
  left: 0;
  width: 70%;
  height: 100%;
  
  /* 引入图片 */
  background-image: url('@/assets/tu.png'); 
  
  /* 核心修改：保持图片比例铺满，且中心对齐 */
  background-size: cover; 
  background-position: center center;
  background-repeat: no-repeat;
  
  /* 可选：加一点深色遮罩，让白色透明框文字更清晰 */
  /* background-color: rgba(0, 0, 0, 0.2); */
  /* background-blend-mode: overlay; */
  
  z-index: 0;
}

.login-card {
  /* 核心修改：宽度改为相对值，适配不同屏幕 */
  width: 90%; 
  max-width: 450px; /* 最大不超过 450px */
  
  padding: 40px 30px; 
  border-radius: 15px; 
  
  /* 透明度设置 */
  background: rgba(255, 255, 255, 0.75); 
  backdrop-filter: blur(10px); 
  
  position: relative; 
  z-index: 10;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
  border: 1px solid rgba(255, 255, 255, 0.5);
  
  /* 增加一个小动画，让登录框加载时有个浮现效果 */
  animation: fadeInDown 0.8s ease-out;
}

/* 简单的浮现动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.title {
  text-align: center;
  margin-bottom: 25px;
  color: #333;
  font-size: 26px; 
  font-weight: bold;
  letter-spacing: 2px;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8); /* 增加文字立体感 */
}

.toggle-mode {
  text-align: right;
  margin-top: 15px;
}

/* 优化输入框样式，使其更通透 */
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.8);
  box-shadow: none !important;
  border: 1px solid #dcdfe6;
}
:deep(.el-input__wrapper.is-focus) {
  border-color: var(--el-color-primary);
  background-color: #fff;
  box-shadow: 0 0 0 1px var(--el-color-primary) inset !important;
}
</style>