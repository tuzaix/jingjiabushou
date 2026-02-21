<template>
  <div class="system-config-container">
    <el-tabs v-model="activeTab" class="config-tabs">
      <el-tab-pane label="韭研公社" name="jiuyan">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span> 获取【韭研公社】每日复盘数据（每日：17:00), 定期更新cURL，测试后保存生效。</span>
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
                  v-model="jiuyanCurlCommand"
                  type="textarea"
                  :rows="10"
                  placeholder="请粘贴 curl 'https://app.jiuyangongshe.com/...' ..."
                />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="saveJiuyanConfig" :loading="jiuyanSaving">保存配置</el-button>
                <el-button type="success" @click="testJiuyanFetch" :loading="jiuyanTesting">测试抓取</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div v-if="jiuyanTestResult" class="result-section">
            <div class="result-header">
              <span>测试结果</span>
              <el-tag :type="jiuyanTestSuccess ? 'success' : 'danger'">{{ jiuyanTestSuccess ? '成功' : '失败' }}</el-tag>
            </div>
            <el-input
              v-model="jiuyanTestResultStr"
              type="textarea"
              :rows="15"
              readonly
              class="result-textarea"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="东方财富" name="eastmoney">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>获取【东方财富】实时竞价数据，不可回溯历史，定期更新cURL，测试后保存生效。</span>
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
                  v-model="eastmoneyCurlCommand"
                  type="textarea"
                  :rows="10"
                  placeholder="请粘贴 curl 'https://vipmoney.eastmoney.com/...' ..."
                />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="saveEastmoneyConfig" :loading="eastmoneySaving">保存配置</el-button>
                <el-button type="success" @click="testEastmoneyFetch" :loading="eastmoneyTesting">测试抓取</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div v-if="eastmoneyTestResult" class="result-section">
            <div class="result-header">
              <span>测试结果</span>
              <el-tag :type="eastmoneyTestSuccess ? 'success' : 'danger'">{{ eastmoneyTestSuccess ? '成功' : '失败' }}</el-tag>
            </div>
            <el-input
              v-model="eastmoneyTestResultStr"
              type="textarea"
              :rows="15"
              readonly
              class="result-textarea"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const activeTab = ref('jiuyan')

// Jiuyan Variables
const jiuyanCurlCommand = ref('')
const jiuyanSaving = ref(false)
const jiuyanTesting = ref(false)
const jiuyanTestResult = ref(null)
const jiuyanTestSuccess = ref(false)

const jiuyanTestResultStr = computed(() => {
  if (!jiuyanTestResult.value) return ''
  return typeof jiuyanTestResult.value === 'string' 
    ? jiuyanTestResult.value 
    : JSON.stringify(jiuyanTestResult.value, null, 2)
})

// Eastmoney Variables
const eastmoneyCurlCommand = ref('')
const eastmoneySaving = ref(false)
const eastmoneyTesting = ref(false)
const eastmoneyTestResult = ref(null)
const eastmoneyTestSuccess = ref(false)

const eastmoneyTestResultStr = computed(() => {
  if (!eastmoneyTestResult.value) return ''
  return typeof eastmoneyTestResult.value === 'string' 
    ? eastmoneyTestResult.value 
    : JSON.stringify(eastmoneyTestResult.value, null, 2)
})

// Jiuyan Methods
const saveJiuyanConfig = async () => {
  if (!jiuyanCurlCommand.value) {
    ElMessage.warning('请输入 cURL 命令')
    return
  }
  
  jiuyanSaving.value = true
  try {
    const response = await axios.post('/api/admin/jiuyan/config', {
      curl: jiuyanCurlCommand.value
    })
    ElMessage.success(response.data.message || '配置保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '保存失败')
  } finally {
    jiuyanSaving.value = false
  }
}

const testJiuyanFetch = async () => {
  jiuyanTesting.value = true
  jiuyanTestResult.value = null
  jiuyanTestSuccess.value = false
  
  try {
    const response = await axios.post('/api/admin/jiuyan/test')
    jiuyanTestResult.value = response.data
    jiuyanTestSuccess.value = response.data.success
    if (response.data.success) {
      ElMessage.success('测试成功')
    } else {
      ElMessage.warning('测试完成但返回失败状态')
    }
  } catch (error) {
    console.error('Test failed:', error)
    jiuyanTestResult.value = error.response?.data || error.message
    ElMessage.error('测试请求失败')
  } finally {
    jiuyanTesting.value = false
  }
}

// Eastmoney Methods
const saveEastmoneyConfig = async () => {
  if (!eastmoneyCurlCommand.value) {
    ElMessage.warning('请输入 cURL 命令')
    return
  }
  
  eastmoneySaving.value = true
  try {
    const response = await axios.post('/api/admin/eastmoney/config', {
      curl: eastmoneyCurlCommand.value
    })
    ElMessage.success(response.data.message || '配置保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '保存失败')
  } finally {
    eastmoneySaving.value = false
  }
}

const testEastmoneyFetch = async () => {
  eastmoneyTesting.value = true
  eastmoneyTestResult.value = null
  eastmoneyTestSuccess.value = false
  
  try {
    const response = await axios.post('/api/admin/eastmoney/test')
    eastmoneyTestResult.value = response.data
    eastmoneyTestSuccess.value = response.data.success
    if (response.data.success) {
      ElMessage.success('测试成功')
    } else {
      ElMessage.warning('测试完成但返回失败状态')
    }
  } catch (error) {
    console.error('Test failed:', error)
    eastmoneyTestResult.value = error.response?.data || error.message
    ElMessage.error('测试请求失败')
  } finally {
    eastmoneyTesting.value = false
  }
}

// Fetch configs on mount
const fetchConfigs = async () => {
  try {
    const jiuyanRes = await axios.get('/api/admin/jiuyan/config')
    if (jiuyanRes.data && jiuyanRes.data.curl) {
      jiuyanCurlCommand.value = jiuyanRes.data.curl
    }
  } catch (error) {
    console.error('Error fetching Jiuyan config:', error)
  }

  try {
    const eastmoneyRes = await axios.get('/api/admin/eastmoney/config')
    if (eastmoneyRes.data && eastmoneyRes.data.curl) {
      eastmoneyCurlCommand.value = eastmoneyRes.data.curl
    }
  } catch (error) {
    console.error('Error fetching Eastmoney config:', error)
  }
}

onMounted(() => {
  fetchConfigs()
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
