<template>
  <div class="admin-container">
    <el-row :gutter="20">
      <!-- Data Import Section -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>数据导入</span>
            </div>
          </template>
          <div class="action-item">
            <h3>导入昨日涨停数据 (Excel)</h3>
            <el-form label-width="100px">
              <el-form-item label="日期">
                <el-date-picker v-model="uploadDate" type="date" placeholder="选择日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
              <el-form-item label="Excel文件">
                 <input type="file" @change="handleFileChange" accept=".xlsx, .xls" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="uploadFile" :loading="uploading">开始导入</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>

      <!-- System Actions Section -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>系统操作</span>
            </div>
          </template>
          
          <div class="action-item">
            <h3>手动触发数据抓取</h3>
            <p>立即抓取当前的竞价数据。</p>
            <el-button type="warning" @click="triggerFetch" :loading="fetching">触发抓取竞价数据</el-button>
          </div>

          <el-divider />

          <div class="action-item">
            <h3>初始化基础数据</h3>
            <p>重新获取所有股票列表和昨日涨停数据（从API）。</p>
            <el-button type="danger" @click="triggerInit" :loading="initializing">初始化数据</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

// Upload Logic
const uploadDate = ref(new Date().toISOString().split('T')[0])
const selectedFile = ref(null)
const uploading = ref(false)

const handleFileChange = (event) => {
  selectedFile.value = event.target.files[0]
}

const uploadFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('date', uploadDate.value)
  
  try {
    const response = await axios.post('/api/upload/yesterday_limit_up', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    ElMessage.success(response.data.message || '导入成功')
  } catch (error) {
    console.error('Upload failed:', error)
    const msg = error.response?.data?.error || error.message
    ElMessage.error('导入失败: ' + msg)
  } finally {
    uploading.value = false
  }
}

// Fetch Logic
const fetching = ref(false)
const triggerFetch = async () => {
  fetching.value = true
  try {
    await axios.post('/api/test/fetch_call_auction')
    ElMessage.success('已触发抓取')
  } catch (error) {
    console.error('Error triggering fetch:', error)
    ElMessage.error('触发抓取失败')
  } finally {
    fetching.value = false
  }
}

// Init Logic
const initializing = ref(false)
const triggerInit = async () => {
  initializing.value = true
  try {
    await axios.post('/api/test/init_data')
    ElMessage.success('已触发初始化')
  } catch (error) {
    console.error('Error triggering init:', error)
    ElMessage.error('触发初始化失败')
  } finally {
    initializing.value = false
  }
}
</script>

<style scoped>
.action-item {
  margin-bottom: 20px;
}
.action-item h3 {
  margin-top: 0;
  margin-bottom: 10px;
}
</style>