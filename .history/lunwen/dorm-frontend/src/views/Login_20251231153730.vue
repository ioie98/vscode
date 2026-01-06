<template>
  <div class="login-container">
    
    <!-- 1. 背景图片层 -->
    <div class="bg-image"></div>

    <!-- 2. 遮罩层：加一层半透明黑色，防止图片太花看不清字 -->
    <div class="bg-overlay"></div>

    <!-- 3. 登录卡片 -->
    <el-card class="login-card">
      <h2 class="title">高校宿舍管理系统</h2>
      
      <div style="text-align: center; margin-bottom: 20px; font-weight: bold; color: #333;">
        {{ isRegister ? '用户注册' : '用户登录' }}
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" size="large" label-width="0">
        <el-form-item prop="role">
          <el-radio-group v-model="form.role" style="width: 100%; justify-content: center;">
            <el-radio :label="1">学生</el-radio>
            <el-radio :label="2">维修工</el-radio>
            <el-radio :label="0">管理员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号/学号" prefix-icon="User" />
        </el-form-item>
        
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

        <template v-if="isRegister && form.role === 1">
          <el-divider content-position="center">宿舍信息</el-divider>
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="form.zoneName" placeholder="园区">
                <el-option label="明德园" value="明德园" />
                <el-option label="求是园" value="求是园" />
                <el-option label="砺尖园" value="砺尖园" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-select v-model="form.buildingName" placeholder="楼栋" filterable allow-create>
                 <el-option v-for="i in 20" :key="i" :label="i + '号楼'" :value="i + '号楼'" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-select v-model="form.roomNumber" placeholder="房号" filterable>
                 <el-option v-for="room in roomOptions" :key="room" :label="room" :value="room" />
              </el-select>
            </el-col>
          </el-row>
          <div style="margin-top: 10px;"></div>
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="form.bedNum" placeholder="床位">
                 <el-option v-for="i in 4" :key="i" :label="i + '号'" :value="i" />
              </el-select>
            </el-col>
            <el-col :span="16"><el-input v-model="form.college" placeholder="学院" /></el-col>
          </el-row>
          <div style="margin-top: 10px;"></div>
          <el-row :gutter="10">
            <el-col :span="12"><el-input v-model="form.major" placeholder="专业" /></el-col>
            <el-col :span="12"><el-input v-model="form.className" placeholder="班级" /></el-col>
          </el-row>
        </template>

        <el-form-item style="margin-top: 20px;">
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleSubmit">
            {{ isRegister ? '注 册' : '登 录' }}
          </el-button>
        </el-form-item>
        
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
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const isRegister = ref(false)

const form = reactive({
  role: 1,
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

const roomOptions = computed(() => {
  const rooms = []
  for (let floor = 1; floor <= 5; floor++) {
    for (let room = 1; room <= 10; room++) {
      const roomNum = `${floor}${room < 10 ? '0' + room : room}`
      rooms.push(roomNum)
    }
  }
  return rooms
})

const toggleMode = () => {
  isRegister.value = !isRegister.value
  form.realName = ''
  form.phone = ''
}

const handleSubmit = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      loading.value = true
      
      if (isRegister.value) {
        if (form.role === 1) form.bedNum = form.bedNum ? Number(form.bedNum) : null;
        axios.post('http://localhost:8080/api/user/register', form)
          .then(res => {
            if (res.data.code === 200) {
              ElMessage.success('注册成功，请登录')
              isRegister.value = false
            } else {
              ElMessage.error(res.data.msg)
            }
          }).finally(() => loading.value = false)
      } else {
        axios.post('http://localhost:8080/api/login', {
          username: form.username,
          password: form.password,
          role: form.role
        }).then(res => {
          if (res.data.code === 200) {
            ElMessage.success('登录成功')
            localStorage.setItem('user', JSON.stringify(res.data.data))
            router.push('/my-dorm')
          } else {
            ElMessage.error(res.data.msg)
          }
        }).finally(() => loading.value = false)
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

/* 核心修改：使用 tu.png 作为背景 */
.bg-image {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background-image: url('@/assets/tu.png'); /* 引用 tu.png */
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: -2; 
}

/* 遮罩层 */
.bg-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.3); /* 半透明黑色遮罩，可调整 0.3 的值 */
  z-index: -1;
}

.login-card {
  width: 90%; 
  max-width: 450px;
  padding: 40px 30px; 
  border-radius: 15px; 
  background: rgba(255, 255, 255, 0.85); 
  backdrop-filter: blur(5px); 
  position: relative; 
  z-index: 10;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
  border: 1px solid rgba(138, 79, 79, 0.5);
  animation: fadeInDown 0.8s ease-out;
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

.title {
  text-align: center;
  margin-bottom: 25px;
  color: #333;
  font-size: 26px; 
  font-weight: bold;
  letter-spacing: 2px;
}

.toggle-mode {
  text-align: right;
  margin-top: 15px;
}

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