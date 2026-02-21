<template>
  <div class="dashboard-container">
    <div class="actions-bar">
      <div class="left-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledDate"
          @change="handleDateChange"
          style="width: 150px; margin-right: 10px;"
        />
        <el-button type="primary" @click="fetchTopN">刷新竞价TopN</el-button>
        <el-button type="success" @click="fetchYesterdayLimitUp">刷新昨日涨停</el-button>
        <el-button type="info" @click="fetchLimitUp925">刷新一字板</el-button>
      </div>
      <div class="right-actions">
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          @change="handleAutoRefreshChange"
        />
        <el-select
          v-model="refreshInterval"
          placeholder="刷新间隔"
          style="width: 120px; margin-left: 10px;"
          @change="handleIntervalChange"
          :disabled="!autoRefresh"
        >
          <el-option label="3秒" :value="3000" />
          <el-option label="5秒" :value="5000" />
          <el-option label="10秒" :value="10000" />
          <el-option label="30秒" :value="30000" />
          <el-option label="60秒" :value="60000" />
        </el-select>
      </div>
    </div>
    
    <el-row :gutter="20">
      <el-col :span="8">
          <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>竞价排名监控 (9:15 / 9:20 / 9:25)</span>
            </div>
          </template>
          <div class="monitor-container" style="display: flex; height: calc(100vh - 180px);">
             <!-- 9:25 Main List -->
             <div class="main-list" style="flex: 1.5; overflow-y: auto; padding-right: 10px; border-right: 1px solid #eee;">
                <div class="list-header-title" style="margin-bottom: 10px; font-weight: bold; color: #e6a23c;">9:25 排名</div>
                <div v-for="item in topNList" :key="item.code" class="top-n-card">
                   <div class="top-n-header">
                      <span class="stock-name">{{ item.name }}</span>
                      <span v-for="sec in getSortedSectors(item.sector).slice(0, 1)" :key="sec" class="stock-tag" :style="getHeatStyle(sec)">{{ sec }}</span>
                      <span v-if="item.consecutive_days > 1" class="stock-tag board-tag">{{ item.consecutive_days }}板</span>
                   </div>
                   <div class="top-n-body">
                      <span class="amount-val amount-925">{{ formatAmount(item.amount) }}</span>
                      <span class="separator">|</span>
                      <span class="amount-val amount-920">{{ formatAmount(item.amount_920) }}</span>
                      <span class="separator">|</span>
                      <span class="amount-val amount-915">{{ formatAmount(item.amount_915) }}</span>
                      <span :class="getChangeClass(item.change_percent)" class="change-val">{{ formatChange(item.change_percent) }}</span>
                   </div>
                </div>
                <div v-if="topNList.length === 0" class="no-data">暂无数据</div>
             </div>
             
             <!-- 9:20 List -->
             <div class="sub-list" style="flex: 1; overflow-y: auto; padding: 0 10px; border-right: 1px solid #eee;">
                <div class="list-header-title" style="margin-bottom: 10px; font-weight: bold; color: #409eff;">9:20 排名</div>
                <div v-for="(item, index) in ranking920List" :key="item.code" class="mini-card">
                   <div class="mini-row" style="justify-content: center; margin-bottom: 0;">
                       <span class="mini-name">{{ item.name }}</span>
                   </div>
                </div>
                <div v-if="ranking920List.length === 0" class="no-data">暂无数据</div>
             </div>

             <!-- 9:15 List -->
             <div class="sub-list" style="flex: 1; overflow-y: auto; padding-left: 10px;">
                <div class="list-header-title" style="margin-bottom: 10px; font-weight: bold; color: #f56c6c;">9:15 排名</div>
                <div v-for="(item, index) in ranking915List" :key="item.code" class="mini-card">
                   <div class="mini-row" style="justify-content: center; margin-bottom: 0;">
                       <span class="mini-name">{{ item.name }}</span>
                   </div>
                </div>
                <div v-if="ranking915List.length === 0" class="no-data">暂无数据</div>
             </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="box-card" :body-style="{ padding: '0px' }">
          <template #header>
            <div class="card-header">
              <span>昨日涨停表现 (9:25)</span>
            </div>
          </template>
          <!-- Custom Layout for Yesterday Limit Up Performance -->
          <div class="yesterday-limit-up-container" style="height: calc(100vh - 180px); overflow-y: auto; padding: 20px;">
             <div v-for="group in groupedYesterdayLimitUp" :key="group.days" class="limit-up-group">
                <div class="group-label">{{ group.days }}板</div>
                <div class="group-items">
                   <div v-for="item in group.items" :key="item.code" class="stock-card">
                      <div class="stock-name">{{ item.name }}</div>
                      <div class="stock-info">
                        <span :class="getChangeClass(item.change_percent)">{{ formatChange(item.change_percent) }}</span>
                      </div>
                      <div class="stock-info amount">
                        {{ formatAmount(item.amount) }}
                      </div>
                      <div class="stock-sector" :style="getSectorStyle(item.sector)">{{ item.sector }}</div>
                   </div>
                </div>
             </div>
             <div v-if="groupedYesterdayLimitUp.length === 0" class="no-data">
                暂无数据
             </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="box-card" :body-style="{ padding: '0px' }">
          <template #header>
            <div class="card-header">
              <span>一字板 (9:25 涨幅10%)</span>
            </div>
          </template>
          <el-table :data="limitUp925List" style="width: 100%" height="calc(100vh - 180px)" stripe :header-cell-style="{background:'#f5f7fa'}">
            <el-table-column prop="code" label="代码" width="80" />
            <el-table-column prop="name" label="名称" width="80" />
            <el-table-column prop="price" label="价格" width="70" />
            <el-table-column prop="change_percent" label="涨幅%" width="70">
                <template #default="scope">
                  <span :style="{ color: 'red' }">
                    {{ scope.row.change_percent }}%
                  </span>
                </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="100">
              <template #default="scope">
                {{ formatAmount(scope.row.amount) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import axios from 'axios'

const topNList = ref([])
const ranking920List = ref([])
const ranking915List = ref([])
const yesterdayLimitUpList = ref([])
const limitUp925List = ref([])
const autoRefresh = ref(true)
const refreshInterval = ref(5000)

// Computed property for grouping yesterday limit up data
const groupedYesterdayLimitUp = computed(() => {
  if (!yesterdayLimitUpList.value || yesterdayLimitUpList.value.length === 0) return []
  
  const groups = {}
  yesterdayLimitUpList.value.forEach(item => {
    const key = item.consecutive_days
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push(item)
  })
  
  // Convert to array and sort by days descending
  const result = Object.keys(groups).map(key => ({
    days: parseInt(key),
    items: groups[key]
  }))
  
  return result.sort((a, b) => b.days - a.days)
})

const splitSector = (sectorStr) => {
  if (!sectorStr) return []
  // Split by common delimiters: space, comma, semicolon, enumeration comma (English or Chinese)
  // Filter out empty strings
  return sectorStr.split(/[\s,;，；、]+/).filter(s => s && s.trim().length > 0)
}

// Compute frequency of each sector in the Top N list
const sectorFrequency = computed(() => {
  const freq = {}
  if (!topNList.value) return freq
  
  topNList.value.forEach(item => {
    if (!item.sector) return
    const sectors = splitSector(item.sector)
    sectors.forEach(sec => {
      freq[sec] = (freq[sec] || 0) + 1
    })
  })
  return freq
})

const maxSectorCount = computed(() => {
  const counts = Object.values(sectorFrequency.value)
  return counts.length ? Math.max(...counts) : 0
})

const getSortedSectors = (sectorStr) => {
  const sectors = splitSector(sectorStr)
  return sectors.sort((a, b) => {
    const countA = sectorFrequency.value[a] || 0
    const countB = sectorFrequency.value[b] || 0
    return countB - countA // Descending
  })
}

const getHeatStyle = (sectorName) => {
  const count = sectorFrequency.value[sectorName] || 0
  
  // Logic: 
  // 1. High absolute count (>=3) -> Solid, Bold Color (Hash-based Hue)
  // 2. Medium absolute count (2) -> Light Background, Colored Text (Hash-based Hue)
  // 3. Low absolute count (1) -> Grey (Noise reduction)
  
  if (count <= 1) {
      // Default/Light style (for single occurrences)
      return { backgroundColor: '#f4f4f5', color: '#909399', border: '1px solid #e9e9eb' } // Grey
  }
  
  // Generate distinct color based on name hash
  let hash = 0
  for (let i = 0; i < sectorName.length; i++) {
    hash = sectorName.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  // Palette of distinct colors (Hue variations)
  // Each entry has: solid (bg), light (bg), text (for light bg), border (for light bg)
  const palette = [
    { solid: '#409eff', light: '#ecf5ff', text: '#409eff', border: '#d9ecff' }, // Blue
    { solid: '#67c23a', light: '#f0f9eb', text: '#67c23a', border: '#e1f3d8' }, // Green
    { solid: '#e6a23c', light: '#fdf6ec', text: '#e6a23c', border: '#faecd8' }, // Orange
    { solid: '#f56c6c', light: '#fef0f0', text: '#f56c6c', border: '#fde2e2' }, // Red
    { solid: '#7c3aed', light: '#f5f3ff', text: '#7c3aed', border: '#ede9fe' }, // Purple
    { solid: '#d946ef', light: '#fdf2f8', text: '#d946ef', border: '#fce7f3' }, // Pink
    { solid: '#059669', light: '#ecfdf5', text: '#059669', border: '#d1fae5' }, // Emerald
    { solid: '#0891b2', light: '#ecfeff', text: '#0891b2', border: '#cffafe' }, // Cyan
    { solid: '#db2777', light: '#fdf2f8', text: '#db2777', border: '#fce7f3' }, // Rose
    { solid: '#ca8a04', light: '#fefce8', text: '#ca8a04', border: '#fef9c3' }, // Yellow-Dark
    { solid: '#4f46e5', light: '#eef2ff', text: '#4f46e5', border: '#e0e7ff' }, // Indigo
    { solid: '#be123c', light: '#fff1f2', text: '#be123c', border: '#ffe4e6' }  // Rose-Dark
  ]
  
  const index = Math.abs(hash) % palette.length
  const colorSet = palette[index]
  
  if (count >= 3) {
      // High Heat: Solid Color Background, White Text
      return { 
          backgroundColor: colorSet.solid, 
          color: '#ffffff', 
          border: `1px solid ${colorSet.solid}`,
          fontWeight: 'bold'
      }
  } else {
      // Medium Heat (count == 2): Light Background, Colored Text
      return { 
          backgroundColor: colorSet.light, 
          color: colorSet.text, 
          border: `1px solid ${colorSet.border}`,
          fontWeight: 'bold'
      }
  }
}

const formatChange = (val) => {
  if (val === undefined || val === null) return '-'
  return val > 0 ? `+${val}%` : `${val}%`
}

const getChangeClass = (val) => {
  if (val > 0) return 'text-red'
  if (val < 0) return 'text-green'
  return ''
}

// Generate a deterministic color style for a sector name
const getSectorStyle = (sectorName) => {
  if (!sectorName) return {}
  
  // Simple hash function
  let hash = 0
  for (let i = 0; i < sectorName.length; i++) {
    hash = sectorName.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  // Predefined palette of background/text color pairs (light bg, dark text)
  const palette = [
    { bg: '#ecf5ff', text: '#409eff', border: '#d9ecff' }, // Blue
    { bg: '#f0f9eb', text: '#67c23a', border: '#e1f3d8' }, // Green
    { bg: '#fdf6ec', text: '#e6a23c', border: '#faecd8' }, // Orange
    { bg: '#fef0f0', text: '#f56c6c', border: '#fde2e2' }, // Red
    { bg: '#f4f4f5', text: '#909399', border: '#e9e9eb' }, // Grey
    { bg: '#e8f3ff', text: '#2d8cf0', border: '#cce1ff' }, // Azure
    { bg: '#fdf2f8', text: '#d03a72', border: '#fce7f3' }, // Pink
    { bg: '#f0fdf4', text: '#16a34a', border: '#dcfce7' }, // Emerald
    { bg: '#fff7ed', text: '#ea580c', border: '#ffedd5' }, // Amber
    { bg: '#f5f3ff', text: '#7c3aed', border: '#ede9fe' }, // Violet
    { bg: '#eff6ff', text: '#2563eb', border: '#dbeafe' }, // Blue-600
    { bg: '#fff1f2', text: '#e11d48', border: '#ffe4e6' }  // Rose
  ]
  
  const index = Math.abs(hash) % palette.length
  const color = palette[index]
  
  return {
    backgroundColor: color.bg,
    color: color.text,
    borderColor: color.border
  }
}

const formatAmount = (val) => {
  if (!val) return '-'
  const num = parseFloat(val)
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿'
  }
  return (num / 10000).toFixed(0) + '万'
}

const getTodayStr = () => {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
const selectedDate = ref(getTodayStr())
const tradingDays = ref(new Set())
let timer = null

const startTimer = () => {
  if (timer) clearInterval(timer)
  if (autoRefresh.value) {
    timer = setInterval(() => {
      fetchTopN()
      fetchLimitUp925()
      // Optional: fetchYesterdayLimitUp usually doesn't change often, but can be added if needed
    }, refreshInterval.value)
  }
}

const handleAutoRefreshChange = (val) => {
  if (val) {
    startTimer()
  } else {
    if (timer) clearInterval(timer)
  }
}

const handleIntervalChange = () => {
  startTimer()
}

const fetchTradingDays = async () => {
  try {
    const response = await axios.get('/api/market/trading_days')
    if (Array.isArray(response.data)) {
      tradingDays.value = new Set(response.data)
    }
  } catch (error) {
    console.error('Error fetching trading days:', error)
  }
}

const disabledDate = (time) => {
  // Always disable future dates
  // Use pure date comparison to avoid timezone/time issues
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (time.getTime() > today.getTime()) {
      return true
  }

  // If tradingDays are loaded, restrict to those days
  if (tradingDays.value.size > 0) {
    const year = time.getFullYear()
    const month = String(time.getMonth() + 1).padStart(2, '0')
    const day = String(time.getDate()).padStart(2, '0')
    const dateStr = `${year}-${month}-${day}`
    return !tradingDays.value.has(dateStr)
  }
  
  // Fallback: disable weekends
  const day = time.getDay()
  return day === 0 || day === 6
}

const handleDateChange = () => {
  fetchTopN()
  fetchYesterdayLimitUp()
  fetchLimitUp925()
}

const fetchTopN = async () => {
  try {
    const response = await axios.get('/api/call_auction/top_n', {
      params: { 
        limit: 50,
        date: selectedDate.value
      }
    })
    topNList.value = response.data
    
    // Also fetch rankings for 9:20 and 9:15
    await fetchRankings()
    
  } catch (error) {
    console.error('Error fetching top N:', error)
  }
}

const fetchRankings = async () => {
  try {
    const dateStr = selectedDate.value
    // 9:20 - 9:21
    const res920 = await axios.get('/api/call_auction/ranking', {
        params: { 
            start_time: '09:20:00', 
            end_time: '09:21:00', 
            limit: 50, 
            date: dateStr 
        }
    })
    ranking920List.value = res920.data
    
    // 9:15 - 9:16
    const res915 = await axios.get('/api/call_auction/ranking', {
        params: { 
            start_time: '09:15:00', 
            end_time: '09:16:00', 
            limit: 50, 
            date: dateStr 
        }
    })
    ranking915List.value = res915.data
  } catch (error) {
    console.error('Error fetching rankings:', error)
  }
}

const fetchLimitUp925 = async () => {
  try {
    const response = await axios.get('/api/call_auction/limit_up_925', {
      params: { date: selectedDate.value }
    })
    limitUp925List.value = response.data
  } catch (error) {
    console.error('Error fetching limit up 925:', error)
  }
}

const fetchYesterdayLimitUp = async () => {
  try {
    // New logic: Use "performance" mode which handles the date calculation on backend
    // and returns merged data (yesterday limit up stocks + today's auction performance)
    const response = await axios.get('/api/yesterday_limit_up', {
      params: { 
        date: selectedDate.value,
        mode: 'performance'
      }
    })
    
    yesterdayLimitUpList.value = response.data
    
    // Convert array to object for v-for if backend returns array
    // Our backend returns array of objects with 'consecutive_days'
    // The computed property 'groupedYesterdayLimitUp' will handle grouping.
    
  } catch (error) {
    console.error('Error fetching yesterday limit up:', error)
  }
}

onMounted(async () => {
  await fetchTradingDays()
  // Ensure selectedDate is valid if it's not in tradingDays (e.g. today is Sunday)
  if (tradingDays.value.size > 0 && !tradingDays.value.has(selectedDate.value)) {
     // Find the closest previous trading day
     // Since tradingDays is a Set, we need to sort it to find the max <= today
     const sortedDays = Array.from(tradingDays.value).sort().reverse()
     const today = getTodayStr()
     const latest = sortedDays.find(d => d <= today)
     if (latest) {
       selectedDate.value = latest
     }
  }

  fetchTopN()
  fetchYesterdayLimitUp()
  fetchLimitUp925()
  
  startTimer()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}
.actions-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.right-actions {
  display: flex;
  align-items: center;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Top N Card Styles */
.top-n-container {
  padding: 5px;
}
.top-n-card {
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 6px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  transition: all 0.2s;
  font-weight: 600;
}
.top-n-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #c6e2ff;
}
.top-n-header {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.stock-name {
  font-size: 15px;
  font-weight: bold;
  color: #303133;
  margin-right: 8px;
}
.stock-tag {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 6px;
  white-space: nowrap;
}
.board-tag {
  background-color: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
}
.top-n-body {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}
.amount-val {
  font-family: monospace;
  font-weight: 500;
}
.amount-925 {
  color: #e6a23c; /* Orange/Gold */
}
.amount-920 {
  color: #409eff; /* Blue */
}
.amount-915 {
  color: #f56c6c; /* Red */
}
.separator {
  margin: 0 8px;
  color: #dcdfe6;
}
.change-val {
  margin-left: auto;
  font-weight: bold;
}

/* Yesterday Limit Up Custom Styles */
.yesterday-limit-up-container {
  padding: 10px;
}

.limit-up-group {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.group-label {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 8px;
  color: #333;
  padding-left: 5px;
  border-left: 3px solid #409eff;
}

.group-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stock-card {
  width: auto;
  min-width: 100px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 8px 12px;
  margin: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  background-color: #fafafa;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  transition: all 0.2s;
  flex-grow: 0;
}

.stock-card:hover {
  background-color: #f0f7ff;
  border-color: #d9ecff;
}

.mini-card {
  padding: 6px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 4px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.2s;
  font-size: 15px;
  font-weight: 600;
}
.mini-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0,0,0,0.08);
  border-color: #c6e2ff;
}
.mini-row {
  display: flex;
  align-items: center;
  margin-bottom: 2px;
}
.rank-badge {
  display: inline-block;
  width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  background-color: #f0f2f5;
  color: #909399;
  border-radius: 50%;
  font-size: 10px;
  margin-right: 6px;
}
.rank-badge.top-3 {
  background-color: #333;
  color: #fff;
}
.mini-name {
  font-weight: bold;
  color: #333;
}
.mini-row-amount {
  color: #606266;
  padding-left: 24px;
  font-family: monospace;
}

/* Reusing stock-name from above but scoped logic might differ slightly, keeping consistent class names */

.stock-info {
  font-size: 14px;
  margin: 0 10px;
  text-align: center;
  white-space: nowrap;
}

.stock-info.amount {
  color: #666;
  font-family: monospace;
}

.stock-sector {
  font-size: 12px;
  white-space: nowrap;
  text-align: center;
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid transparent;
  font-weight: 500;
  margin-left: 10px;
}

.text-red {
  color: #f56c6c;
}

.text-green {
  color: #67c23a;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 20px;
}
</style>