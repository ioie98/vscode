<template>
  <el-card>
    <div slot="header" class="clearfix">
      <span style="font-weight: bold;">卫生检查记录</span>
      <el-tag v-if="user.role === 0" style="margin-left: 10px;">全校视图</el-tag>
    </div>
    
    <el-table :data="tableData" stripe style="width: 100%; margin-top: 20px;">
      <!-- 新增：宿舍位置列 (管理员看的时候很有用) -->
      <el-table-column label="宿舍" width="150">
        <template #default="{ row }">
          <span v-if="row.buildingName">
            {{ row.buildingName }} {{ row.roomNumber }}
          </span>
          <span v-else>本宿舍</span>
        </template>
      </el-table-column>

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
  // 逻辑修改：只有普通学生(role=1)且无宿舍ID才拦截，管理员直接放行
  if (user.role === 1 && !user.dormId) return
  
  axios.get(`http://localhost:8080/api/common/hygiene/list`, {
    params: {
      dormId: user.dormId,
      role: user.role
    }
  }).then(res => {
      if (res.data.code === 200) {
        tableData.value = res.data.data
      }
    })
}

onMounted(() => {
  fetchData()
})
</script>