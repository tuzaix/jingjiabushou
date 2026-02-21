<template>
  <div class="admin-container">
    <el-row :gutter="20">
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
.admin-container {
  padding: 20px;
}
.action-item {
  margin-bottom: 20px;
}
.action-item h3 {
  margin-top: 0;
  margin-bottom: 10px;
}
</style>