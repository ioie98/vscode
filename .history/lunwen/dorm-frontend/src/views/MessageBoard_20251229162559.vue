<template>
  <div class="msg-container">
    <el-button type="primary" icon="Edit" style="margin-bottom: 20px;" @click="handleAdd">写留言</el-button>
    <div class="card-list">
      <div v-for="(item, index) in list" :key="index" class="note-card" :style="{ backgroundColor: item.color || '#f0f9eb' }">
        <h3 class="note-title">{{ item.title }}</h3>
        <p class="note-content">{{ item.content }}</p>
        <div class="note-footer">
          <span>{{ item.author }}</span>
          <br>
          <span style="font-size: 12px; color: #666">{{ item.createTime ? item.createTime.substring(0,10) : '' }}</span>
        </div>
        <!-- 胶带效果 -->
        <div class="tape"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const list = ref([])
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')

const fetchData = () => {
  axios.get('http://localhost:8080/api/common/message/list').then(res => {
    if(res.data.code === 200) list.value = res.data.data
  })
}

const handleAdd = () => {
  // 简单模拟直接发一条
  const msg = {
    title: '新留言',
    content: '这是一条测试留言内容...',
    author: currentUser.realName || currentUser.username,
    color: '#e1f3d8'
  }
  axios.post('http://localhost:8080/api/common/message/add', msg).then(res => {
    if(res.data.code === 200) {
      ElMessage.success('发布成功')
      fetchData()
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
.note-card:nth-child(even) { transform: rotate(2deg); background-color: #fdf6ec !important; }
.note-card:hover { transform: scale(1.05); z-index: 10; }
.tape {
  position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
  width: 100px; height: 30px; background-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.note-title { margin-top: 10px; font-size: 18px; color: #333; }
.note-content { margin-top: 10px; color: #555; line-height: 1.6; word-break: break-all;}
.note-footer { margin-top: 20px; text-align: right; font-weight: bold;}
</style>