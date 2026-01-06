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
  
  /* ============ 核心修改开始 ============ */
  /* 1. 引入图片 (注意：@ 符号代表 src 目录) */
  background-image: url('@/assets/tu.png'); 
  
  /* 2. 图片铺满全屏，不拉伸变形 */
  background-size: cover;
  
  /* 3. 图片居中显示 */
  background-position: center;
  
  /* 4. 防止图片重复 */
  background-repeat: no-repeat;
  
  /* 5. (可选) 加一点模糊效果，让前面的登录框更清晰，不需要就删掉这行 */
  /* filter: blur(2px); */
  /* ============ 核心修改结束 ============ */
}

/* 原来的动画代码删掉了，因为静态图片背景不需要动 */

.login-card {
  width: 450px; 
  padding: 30px; 
  border-radius: 12px; 
  /* 背景稍微调白一点，防止背景图太花看不清字 */
  background: rgba(255, 255, 255, 0.5); 
  backdrop-filter: blur(5px); 
  position: relative; 
  z-index: 10;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* 加深阴影 */
}

.title {
  text-align: center;
  margin-bottom: 10px;
  color: #333;
  font-size: 26px; 
  font-weight: bold;
}
.toggle-mode {
  text-align: right;
  margin-top: 10px;
}
</style>