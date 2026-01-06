<template>
  <el-card>
    <div slot="header" class="clearfix">
      <span>卫生检查记录 (宿舍ID: {{ user.dormId }})</span>
    </div>
    
    <el-table :data="tableData" stripe style="width: 100%; margin-top: 20px;">
      <el-table-column prop="checkDate" label="检查日期" width="180">
        <template #default="scope">
          {{ scope.row.checkDate ? scope.row.checkDate.substring(0, 10) : '' }}
        </template>
      </el-table-column>
      <el-table-column prop="score" label="得分" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.score >= 90 ? 'success' : 'warning'">
            {{ scope.row.score }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="检查情况 / 备注" />
    </el-table>

    <div v-if="tableData.length === 0" style="text-align: center; color: #999; margin-top: 20px;">
      暂无检查记录
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tableData = ref([])
const user = JSON.parse(localStorage.getItem('user') || '{}')

const fetchData = () => {
  if (!user.dormId) return
  
  axios.get(`http://localhost:8080/api/common/hygiene/list?dormId=${user.dormId}`)
    .then(res => {
      if (res.data.code === 200) {
        tableData.value = res.data.data
      }
    })
}

onMounted(() => {
  fetchData()
})
</script>