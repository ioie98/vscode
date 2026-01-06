<template>
  <div class="msg-container">
    <!-- 顶部按钮 -->
    <el-button type="primary" icon="Edit" style="margin-bottom: 20px;" @click="openDialog">
      写留言
    </el-button>

    <!-- 留言卡片列表 -->
    <div class="card-list">
      <div v-for="(item, index) in list" :key="index" class="note-card" :style="{ backgroundColor: item.color || '#f0f9eb' }">
        <h3 class="note-title">{{ item.title }}</h3>
        <p class="note-content">{{ item.content }}</p>
        <div class="note-footer">
          <span>-- {{ item.author }}</span>
          <br>
          <span style="font-size: 12px; color: #666">
            {{ item.createTime ? item.createTime.replace('T', ' ').substring(0, 16) : '' }}
          </span>
        </div>
        <!-- 胶带效果 -->
        <div class="tape"></div>
      </div>
    </div>

    <!-- 新增：写留言的弹窗 -->
    <el-dialog v-model="dialogVisible" title="发布新留言" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input 
            v-model="form.content" 
            type="textarea" 
            :rows="4" 
            placeholder="请输入想要说的话..." 
          />
        </el-form-item>
        <el-form-item label="便签颜色">
          <!-- 简单的颜色选择器 -->
          <el-radio-group v-model="form.color">
            <el-radio label="#f0f9eb">绿色</el-radio>
            <el-radio label="#d9ecff">蓝色</el-radio>
            <el-radio label="#fdf6ec">黄色</el-radio>
            <el-radio label="#faecd8">橙色</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitMessage">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const list = ref([])
const dialogVisible = ref(false)
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')

// 表单数据
const form = reactive({
  title: '',
  content: '',
  color: '#f0f9eb' // 默认绿色
})

// 获取留言列表
const fetchData = () => {
  axios.get('http://localhost:8080/api/common/message/list').then(res => {
    if(res.data.code === 200) {
      list.value = res.data.data
    }
  })
}

// 打开弹窗
const openDialog = () => {
  form.title = ''
  form.content = ''
  form.color = '#f0f9eb'
  dialogVisible.value = true
}

// 提交留言
const submitMessage = () => {
  if (!form.title || !form.content) {
    ElMessage.warning('标题和内容不能为空')
    return
  }

  const msg = {
    title: form.title,
    content: form.content,
    color: form.color,
    author: currentUser.realName || currentUser.username
  }

  axios.post('http://localhost:8080/api/common/message/add', msg).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('发布成功')
      dialogVisible.value = false // 关闭弹窗
      fetchData() // 刷新列表
    } else {
      ElMessage.error('发布失败')
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.msg-container { padding: 20px; }
.card-list { display: flex; flex-wrap: wrap; gap: 30px; }
.note-card {
  width: 250px; min-height: 200px; padding: 20px;
  position: relative; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
  transform: rotate(-2deg); transition: transform 0.3s;
  border-radius: 4px;
}
.note-card:nth-child(even) { transform: rotate(2deg);  }
.note-card:hover { transform: scale(1.05); z-index: 10; }
.tape {
  position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
  width: 100px; height: 30px; background-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.note-title { margin-top: 10px; font-size: 18px; color: #333; border-bottom: 1px dashed #ccc; padding-bottom: 5px;}
.note-content { margin-top: 10px; color: #555; line-height: 1.6; word-break: break-all; min-height: 80px;}
.note-footer { margin-top: 20px; text-align: right; font-weight: bold;}
</style>