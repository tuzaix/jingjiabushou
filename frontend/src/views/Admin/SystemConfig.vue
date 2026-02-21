<template>
  <div class="system-config-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>外部数据源配置 (韭研公社)</span>
        </div>
      </template>
      
      <div class="config-section">
        <el-alert
          title="说明：请从浏览器开发者工具中复制相关请求的 cURL (bash) 命令，粘贴到下方文本框中。系统将自动提取 URL、Headers 和 Body 信息。"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 20px;"
        />
        
        <el-form label-position="top">
          <el-form-item label="cURL 命令">
            <el-input
              v-model="curlCommand"
              type="textarea"
              :rows="10"
              placeholder="请粘贴 curl 'https://app.jiuyangongshe.com/...' ..."
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
            <el-button type="success" @click="testFetch" :loading="testing">测试抓取</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="testResult" class="result-section">
        <div class="result-header">
          <span>测试结果</span>
          <el-tag :type="testSuccess ? 'success' : 'danger'">{{ testSuccess ? '成功' : '失败' }}</el-tag>
        </div>
        <el-input
          v-model="testResultStr"
          type="textarea"
          :rows="15"
          readonly
          class="result-textarea"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const curlCommand = ref('')
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const testSuccess = ref(false)

const testResultStr = computed(() => {
  if (!testResult.value) return ''
  return typeof testResult.value === 'string' 
    ? testResult.value 
    : JSON.stringify(testResult.value, null, 2)
})

const fetchConfig = async () => {
  try {
    const response = await axios.get('/api/admin/jiuyan/config')
    // We don't reconstruct curl command from config yet, maybe just show status
    // Or if we want to show current config, we can display it.
    // For now, let's just leave the textarea empty or maybe show "Config exists"
    if (response.data && response.data.url) {
      // Maybe show current headers/url in a separate view?
      // curlCommand.value = `Current Config:\nURL: ${response.data.url}\n...`
    }
  } catch (error) {
    console.error('Error fetching config:', error)
  }
}

const saveConfig = async () => {
  if (!curlCommand.value) {
    ElMessage.warning('请输入 cURL 命令')
    return
  }
  
  saving.value = true
  try {
    const response = await axios.post('/api/admin/jiuyan/config', {
      curl: curlCommand.value
    })
    ElMessage.success(response.data.message || '配置保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '保存失败')
  } finally {
    saving.value = false
  }
}

const testFetch = async () => {
  testing.value = true
  testResult.value = null
  try {
    // Default date to yesterday or let backend decide
    const response = await axios.post('/api/admin/jiuyan/sync', {
      // date: '2026-02-13' // Optional
    })
    testSuccess.value = true
    testResult.value = response.data.data || response.data
    ElMessage.success('测试抓取成功')
  } catch (error) {
    testSuccess.value = false
    testResult.value = error.response?.data?.error || error.message
    ElMessage.error('测试抓取失败')
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<style scoped>
.system-config-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.result-section {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.result-textarea :deep(.el-textarea__inner) {
  font-family: monospace;
  font-size: 12px;
}
</style>
