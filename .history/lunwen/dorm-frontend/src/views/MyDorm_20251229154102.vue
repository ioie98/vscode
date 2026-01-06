<template>
  <el-card class="box-card">
    <!-- 顶部操作 -->
    <div style="margin-bottom: 20px;">
      <el-button type="success" icon="Check">选择床位</el-button>
      <div style="float: right;">
        <el-button icon="Grid" circle />
        <el-button icon="Download" circle />
        <el-button icon="Printer" circle />
      </div>
    </div>

    <!-- 表格 -->
    <el-table :data="tableData" style="width: 100%" stripe header-cell-style="background:#f5f7fa;">
      <el-table-column prop="zone_name" label="宿舍区" width="120" />
      <el-table-column prop="building_name" label="楼栋" width="100" />
      <el-table-column prop="room_number" label="寝室" width="100" />
      <el-table-column prop="bed_num" label="床位号" width="80" align="center" />
      <el-table-column prop="real_name" label="姓名" width="120" />
      <el-table-column prop="username" label="学号" width="150" />
      <el-table-column prop="college" label="学院" width="150" />
      <el-table-column prop="major" label="专业" width="150" />
      <el-table-column prop="class_name" label="班级" />
    </el-table>

    <!-- 分页 (模拟) -->
    <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
      <el-pagination background layout="prev, pager, next" :total="tableData.length" :page-size="10" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const tableData = ref([])
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')

const fetchData = () => {
  if (!currentUser.dormId) {
    ElMessage.warning('您暂未分配宿舍')
    return
  }
  
  // 调用刚才写的后端接口
  axios.get(`http://localhost:8080/api/my-dorm/list?dormId=${currentUser.dormId}`)
    .then(res => {
      if (res.data.code === 200) {
        // 后端返回的Map key是驼峰还是下划线取决于MyBatis配置
        // 如果配置了 map-underscore-to-camel-case=true，则是驼峰
        tableData.value = res.data.data
      }
    })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.box-card {
  min-height: 500px;
}
</style>