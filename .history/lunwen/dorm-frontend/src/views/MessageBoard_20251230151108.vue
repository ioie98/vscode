<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">留言板</span>
        <div class="header-actions">
          <el-button type="primary" icon="Edit" @click="openDialog">写留言</el-button>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px;" />
        </div>
      </div>

      <div class="card-list">
        <!-- 注意：这里 :style 会动态绑定数据库存的颜色 -->
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
          <div class="tape"></div>
        </div>
        <div v-if="list.length === 0" style="text-align: center; color: #999; margin-top: 20px; width: 100%;">
          暂无留言
        </div>
      </div>

      <el-dialog v-model="dialogVisible" title="发布新留言" width="500px">
        <el-form :model="form" label-width="80px">
          <el-form-item label="标题" prop="title">
            <el-input v-model="form.title" placeholder="请输入标题" />
          </el-form-item>
          <el-form-item label="内容" prop="content">
            <el-input 
              v-model="form.content" 
              type="textarea" 
              :rows="4" 
              placeholder="请输入想要说的话..." 
            />
          </el-form-item>
          <el-form-item label="便签颜色">
            <el-radio-group v-model="form.color">
              <el-radio label="#f0f9eb" style="color: #67c23a; font-weight: bold;">绿色</el-radio>
              <el-radio label="#d9ecff" style="color: #409eff; font-weight: bold;">蓝色</el-radio>
              <el-radio label="#fdf6ec" style="color: #e6a23c; font-weight: bold;">黄色</el-radio>
              <el-radio label="#faecd8" style="color: #d08d00; font-weight: bold;">橙色</el-radio>
              <el-radio label="#fde2e2" style="color: #f56c6c; font-weight: bold;">红色</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitMessage">发布</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const list = ref([])
const dialogVisible = ref(false)
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')

const form = reactive({
  title: '',
  content: '',
  color: '#f0f9eb' 
})

const fetchData = () => {
  // 修改IP为你的实际后端地址
  axios.get('http://192.168.12.26:8080/api/common/message/list').then(res => {
    if(res.data.code === 200) {
      list.value = res.data.data
    }
  })
}

const openDialog = () => {
  form.title = ''
  form.content = ''
  form.color = '#f0f9eb'
  dialogVisible.value = true
}

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

  // 修改IP为你的实际后端地址
  axios.post('http://192.168.12.26:8080/api/common/message/add', msg).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('发布成功')
      dialogVisible.value = false 
      fetchData() 
    } else {
      ElMessage.error('发布失败')
    }
  }).catch(err => {
    console.error("发布留言失败:", err);
    ElMessage.error("发布失败，请检查网络或控制台错误");
  });
}

onMounted(() => {
  fetchData()
})
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
  background-color: #fdfdfd; /* 稍微给个背景色 */
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
.card-list { display: flex; flex-wrap: wrap; gap: 30px; padding: 20px; }

.note-card {
  width: 250px; 
  min-height: 200px; 
  padding: 20px;
  position: relative; 
  box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
  transform: rotate(-2deg); 
  transition: transform 0.3s;
  border-radius: 4px;
  /* 关键修改：去掉了这里的 background-color，完全依赖 inline-style */
}

/* 关键修改：去掉 background-color !important，只保留旋转效果 */
.note-card:nth-child(even) { 
  transform: rotate(2deg); 
  /* background-color: ...  这里删掉了！ */
}

.note-card:hover { 
  transform: scale(1.05) rotate(0deg); 
  z-index: 10; 
  box-shadow: 4px 4px 15px rgba(0,0,0,0.2);
}

.tape {
  position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
  width: 110px; height: 35px; 
  background-color: rgba(255, 255, 255, 0.4);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border-radius: 2px;
  backdrop-filter: blur(2px);
}
.note-title { 
  margin-top: 15px; 
  font-size: 18px; 
  color: #333; 
  border-bottom: 2px dashed rgba(0,0,0,0.1); 
  padding-bottom: 5px;
  font-family: 'Comic Sans MS', cursive, sans-serif; /* 换个字体增加趣味性 */
}
.note-content { 
  margin-top: 10px; 
  color: #555; 
  line-height: 1.6; 
  word-break: break-all; 
  min-height: 80px;
  font-size: 14px;
}
.note-footer { 
  margin-top: 20px; 
  text-align: right; 
  font-weight: bold;
  font-size: 12px;
  color: rgba(0,0,0,0.5);
}
</style>