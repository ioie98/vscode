<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix" style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold; font-size: 16px;">水电费管理</span>
        <div class="header-actions">
          <el-tag v-if="user.role === 0" style="margin-right: 10px; margin-bottom: 10px;">全校账单</el-tag>
          <el-button v-if="user.role === 0" type="primary" icon="Plus" style="margin-bottom: 10px;" @click="openDialog(false)">发布账单</el-button>
          <el-button icon="Refresh" circle @click="fetchData" style="margin-left: 10px;" />
        </div>
      </div>

      <el-table 
        :data="tableData" 
        border 
        stripe 
        style="width: 100%" 
        v-loading="loading"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
        :row-style="{ height: '45px' }"
      >
        <el-table-column label="宿舍" width="240">
          <template #default="{ row }">
            {{ row.zoneName }} {{ row.buildingName }} - {{ row.roomNumber }}
          </template>
        </el-table-column>
        
        <el-table-column prop="month" label="月份" width="157" align="center" />
        
        <el-table-column label="用量详情" width="200">
          <template #default="{ row }">
            <div>水: {{ row.waterUsage }} 吨</div>
            <div>电: {{ row.electricUsage }} 度</div>
          </template>
        </el-table-column>

        <el-table-column label="费用详情" width="200">
          <template #default="{ row }">
            <div>水费: ￥{{ row.waterCost }}</div>
            <div>电费: ￥{{ row.electricCost }}</div>
          </template>
        </el-table-column>

        <el-table-column prop="totalCost" label="总金额" width="120" align="center">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: bold;">￥{{ row.totalCost }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '已缴费' : '未缴费' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <!-- 学生：缴费 -->
            <el-button 
              v-if="user.role === 1 && row.status === 0" 
              type="primary" 
              size="small" 
              @click="handlePay(row)"
            >
              立即缴费
            </el-button>
            
            <!-- 管理员：编辑 & 删除 -->
            <template v-if="user.role === 0">
              <el-button 
                type="primary" 
                size="small" 
                icon="Edit"
                @click="openDialog(true, row)"
              >
                编辑
              </el-button>
              <el-button 
                type="danger" 
                size="small" 
                icon="Delete"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
            
            <span v-if="user.role === 1 && row.status === 1" style="color: #67c23a; font-size: 12px;">已完成</span>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 20px; text-align: right;">
        <!-- 分页组件配置 -->
        <el-pagination 
          background 
          layout="total, prev, pager, next" 
          :total="total" 
          :page-sizes="[15, 30, 50]" 
          :page-size="pageSize" 
          @size-change="handleSizeChange" 
          @current-change="handleCurrentChange" 
        />
      </div>

      <!-- 管理员发布/编辑账单弹窗 -->
      <el-dialog v-model="dialogVisible" :title="isEditMode ? '修改水电费账单' : '发布水电费账单'" width="500px">
        <el-form :model="form" label-width="100px">
          <el-form-item label="选择宿舍">
            <el-select v-model="form.dormId" placeholder="请选择" filterable style="width: 100%" :disabled="isEditMode">
              <el-option
                v-for="dorm in dormList"
                :key="dorm.id"
                :label="dorm.zoneName + ' ' + dorm.buildingName + '-' + dorm.roomNumber"
                :value="dorm.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="月份">
            <el-date-picker 
              v-model="form.month" 
              type="month" 
              placeholder="选择月份" 
              format="YYYY-MM" 
              value-format="YYYY-MM" 
              style="width: 100%" 
            />
          </el-form-item>
          
          <el-divider content-position="center">费用计算 (自动)</el-divider>
          <div style="text-align: center; margin-bottom: 15px; color: #999; font-size: 12px;">
            计费标准：水费 3元/吨，电费 0.5元/度
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="用水(吨)">
                <el-input-number v-model="form.waterUsage" :precision="1" :step="0.1" :min="0" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="水费(元)">
                <el-input :model-value="computedWaterCost" readonly disabled />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="用电(度)">
                <el-input-number v-model="form.electricUsage" :precision="1" :step="1" :min="0" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="电费(元)">
                <el-input :model-value="computedElectricCost" readonly disabled />
              </el-form-item>
            </el-col>
          </el-row>
          
          <div style="text-align: right; margin-top: 10px; font-size: 16px;">
            总计：<span style="color: #f56c6c; font-weight: bold; font-size: 20px;">￥{{ computedTotal }}</span>
          </div>

        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)
const user = JSON.parse(localStorage.getItem('user') || '{}')

const dialogVisible = ref(false)
const isEditMode = ref(false)
const dormList = ref([])

const form = reactive({
  id: null,
  dormId: null,
  month: '',
  waterUsage: 0,
  electricUsage: 0
})

const computedWaterCost = computed(() => (form.waterUsage * 3).toFixed(2))
const computedElectricCost = computed(() => (form.electricUsage * 0.5).toFixed(2))
const computedTotal = computed(() => (parseFloat(computedWaterCost.value) + parseFloat(computedElectricCost.value)).toFixed(2))

const fetchData = () => {
  if (user.role === 1 && !user.dormId) {
    tableData.value = []; return;
  }
  loading.value = true
  axios.get('http://localhost:8080/api/utility/list', {
    params: {
      role: user.role,
      dormId: user.dormId,
      pageNum: currentPage.value,
      pageSize: pageSize.value
    }
  }).then(res => {
    if(res.data.code === 200) {
      tableData.value = res.data.data.list
      total.value = res.data.data.total
    }
  }).finally(() => loading.value = false)
}

// 切换页码
const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

// 新增：切换每页显示数量
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1 // 切换每页大小时，通常重置回第一页
  fetchData()
}

const handlePay = (row) => {
  ElMessageBox.confirm(`确认支付 ￥${row.totalCost} 吗？`, '缴费确认', { confirmButtonText: '支付' })
    .then(() => {
      axios.post('http://localhost:8080/api/utility/pay', { id: row.id }).then(res => {
        if(res.data.code === 200) {
          ElMessage.success('缴费成功')
          fetchData()
        }
      })
    })
}

const openDialog = (isEdit, row) => {
  if (dormList.value.length === 0) {
    axios.get('http://localhost:8080/api/dorm/list').then(res => {
      if(res.data.code === 200) dormList.value = res.data.data
    })
  }
  
  isEditMode.value = isEdit
  if (isEdit && row) {
    form.id = row.id
    form.dormId = row.dormId
    form.month = row.month
    form.waterUsage = row.waterUsage
    form.electricUsage = row.electricUsage
  } else {
    form.id = null
    form.dormId = null
    form.month = ''
    form.waterUsage = 0
    form.electricUsage = 0
  }
  dialogVisible.value = true
}

const submitForm = () => {
  if(!form.dormId || !form.month) return ElMessage.warning('请选择宿舍和月份')
  
  const url = isEditMode.value ? 'http://localhost:8080/api/utility/update' : 'http://localhost:8080/api/utility/add'
  
  axios.post(url, form).then(res => {
    if(res.data.code === 200) {
      ElMessage.success(isEditMode.value ? '修改成功' : '发布成功')
      dialogVisible.value = false
      fetchData()
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除这条账单记录吗？', '警告', { type: 'warning' }).then(() => {
    axios.post('http://localhost:8080/api/utility/delete', { id: row.id }).then(res => {
      if (res.data.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      } else {
        ElMessage.error('删除失败')
      }
    })
  }).catch(() => {})
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.app-container { padding: 0; background-color: transparent; }
.box-card { min-height: calc(100vh - 100px); border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.el-card__header { border-bottom: 1px solid #ebeef5; padding: 18px 20px; }
</style>