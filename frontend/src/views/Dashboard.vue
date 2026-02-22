<template>
  <div class="dashboard-container">
    <div class="actions-bar" style="justify-content: flex-end;">
      <div class="right-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledDate"
          @change="handleDateChange"
          style="width: 140px; margin-right: 15px;"
        />
        
        <div style="display: flex; align-items: center; margin-right: 10px;">
            <el-icon style="font-size: 18px; margin-right: 5px; color: #409EFF;"><Refresh /></el-icon>
            <el-switch
              v-model="autoRefresh"
              @change="handleAutoRefreshChange"
            />
        </div>

        <el-select
          v-model="refreshInterval"
          placeholder="间隔"
          style="width: 80px;"
          @change="handleIntervalChange"
          :disabled="!autoRefresh"
          size="default"
        >
          <el-option label="3s" :value="3000" />
          <el-option label="5s" :value="5000" />
          <el-option label="10s" :value="10000" />
          <el-option label="30s" :value="30000" />
          <el-option label="60s" :value="60000" />
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
             <!-- Rank Column -->
             <div style="flex: 0 0 50px; display: flex; flex-direction: column; border-right: 1px solid #eee; height: 100%;">
                <div class="list-header-title" style="margin-bottom: 10px; font-weight: bold; color: #909399; text-align: center; flex-shrink: 0;">序号</div>
                <div class="rank-list sub-list" ref="rankListRef" @scroll="handleScroll('rank')" style="flex: 1; overflow-y: auto;">
                   <div v-for="(item, index) in processedTopNList" :key="'rank-' + index" 
                        class="rank-card"
                        :class="{ 'is-hovered': hoveredCode === item.code }"
                        @mouseenter="handleMouseEnter(item.code)" 
                        @mouseleave="handleMouseLeave">
                      <div class="rank-number" :class="getRankClass(index)">{{ index + 1 }}</div>
                   </div>
                </div>
             </div>

             <!-- 9:25 Main List -->
            <div style="flex: 2; display: flex; flex-direction: column; border-right: 1px solid #eee; padding-right: 10px; padding-left: 10px; height: 100%;">
               <div class="list-header-title" style="margin-bottom: 10px; font-weight: bold; color: #e6a23c; text-align: center; flex-shrink: 0;">9:25 排名</div>
               <div class="main-list" ref="mainListRef" @scroll="handleScroll('main')" style="flex: 1; overflow-y: auto;">
                  <div v-for="(item, index) in processedTopNList" :key="item.code" 
                       class="top-n-card" 
                       :class="{ 'is-hovered': hoveredCode === item.code }"
                       @mouseenter="handleMouseEnter(item.code)" 
                       @mouseleave="handleMouseLeave">
                     <div class="top-n-header">
                        <span class="stock-name">{{ item.name }}</span>
                        <span v-for="sec in getSortedSectors(item.sector).slice(0, 1)" :key="sec" class="stock-tag" :style="getHeatStyle(sec)">{{ sec }}</span>
                        <span v-if="getBoardTagInfo(item)" 
                              class="stock-tag" 
                              :class="getBoardTagInfo(item).class">
                          {{ getBoardTagInfo(item).text }}
                        </span>
                     </div>
                     <div class="top-n-body">
                        <span class="amount-val amount-925">{{ formatAmount(item.amount) }}</span>
                        <span class="separator">|</span>
                        <span class="amount-val amount-920">{{ formatAmount(item.amount_920) }}</span>
                        <span class="separator">|</span>
                        <span class="amount-val amount-915">{{ formatAmount(item.amount_915) }}</span>
                        <span :class="getChangeClass(item.change_percent)" class="change-val">{{ formatChange(item.change_percent) }}</span>
                     </div>
                     
                     <!-- Rank Change Indicator -->
                     <div v-if="getRankChangeInfo(item.code, index)" 
                          class="rank-change-indicator"
                          :style="{ color: getRankChangeInfo(item.code, index).color }">
                        <span class="rank-change-text">{{ getRankChangeInfo(item.code, index).text }}</span>
                        <el-icon><component :is="getRankChangeInfo(item.code, index).icon" /></el-icon>
                     </div>
                  </div>
                  <div v-if="processedTopNList.length === 0" class="no-data">暂无数据</div>
               </div>
            </div>
            
            <!-- 9:20 List -->
            <div style="flex: 1; display: flex; flex-direction: column; border-right: 1px solid #eee; padding: 0 10px; height: 100%;">
               <div class="list-header-title" style="margin-bottom: 10px; font-weight: bold; color: #409eff; text-align: center; flex-shrink: 0;">9:20 排名</div>
               <div class="sub-list" ref="subList920Ref" @scroll="handleScroll('sub920')" style="flex: 1; overflow-y: auto;">
                  <div v-for="(item, index) in ranking920List" :key="item.code" 
                        class="mini-card"
                        :class="{ 'is-hovered': hoveredCode === item.code }"
                        @mouseenter="handleMouseEnter(item.code)" 
                        @mouseleave="handleMouseLeave">
                     <div class="mini-row" style="margin-bottom: 0;">
                         <span class="mini-name">{{ item.name }}</span>
                     </div>
                  </div>
                  <div v-if="ranking920List.length === 0" class="no-data">暂无数据</div>
               </div>
            </div>

            <!-- 9:15 List -->
            <div style="flex: 1; display: flex; flex-direction: column; padding-left: 10px; height: 100%;">
               <div class="list-header-title" style="margin-bottom: 10px; font-weight: bold; color: #f56c6c; text-align: center; flex-shrink: 0;">9:15 排名</div>
               <div class="sub-list" ref="subList915Ref" @scroll="handleScroll('sub915')" style="flex: 1; overflow-y: auto;">
                   <div v-for="(item, index) in ranking915List" :key="item.code" 
                         class="mini-card"
                         :class="{ 'is-hovered': hoveredCode === item.code }"
                         @mouseenter="handleMouseEnter(item.code)" 
                         @mouseleave="handleMouseLeave">
                      <div class="mini-row" style="margin-bottom: 0;">
                          <span class="mini-name">{{ item.name }}</span>
                      </div>
                   </div>
                   <div v-if="ranking915List.length === 0" class="no-data">暂无数据</div>
                </div>
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
             <div v-for="group in groupedYesterdayLimitUp" :key="group.key" class="limit-up-group">
                <div class="group-label" :style="group.rate >= 50 ? { color: '#f56c6c' } : {}">{{ group.label }}</div>
                <div class="group-items">
                   <div v-for="item in group.items" :key="item.code" class="stock-card"
                        :class="{ 'is-hovered': hoveredCode === item.code }"
                        @mouseenter="handleMouseEnter(item.code)" 
                        @mouseleave="handleMouseLeave">
                     <div v-if="item.code.startsWith('30') || item.code.startsWith('688')" class="limit-up-20cm-badge">20cm</div>
                     <div v-if="item.edition && item.edition !== 0 && (item.consecutive_days > item.edition)" class="edition-badge">
                        {{ item.consecutive_days }}天{{ item.edition }}板
                     </div>
                 <div class="stock-name">{{ item.name }}</div>
                      <div class="stock-info">
                        <span :class="getChangeClass(item.change_percent)">{{ formatChange(item.change_percent) }}</span>
                      </div>
                      <div class="stock-info amount" title="成交额 / 涨停委买额">
                        <span>{{ formatAmount(item.bidding_amount) }}</span>
                        <span style="color: #909399; margin: 0 4px;">/</span>
                        <span style="color: #E6A23C;">{{ formatAmount(item.asking_amount) }}</span>
                      </div>
                      <div style="display: flex; margin-left: 10px;">
                        <span v-for="sec in getSortedLimitUpSectors(item.sector).slice(0, 2)" :key="sec" class="stock-tag" :style="getLimitUpHeatStyle(sec)">{{ sec }}</span>
                      </div>
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
        <div style="height: calc(100vh - 120px); display: flex; flex-direction: column; gap: 20px;">
          <!-- 1. Market Sentiment -->
          <el-card class="box-card" :body-style="{ padding: '15px' }" style="flex: 0 0 auto;">
            <template #header>
              <div class="card-header">
                <span>大局观 (9:25)</span>
              </div>
            </template>
            <div class="sentiment-grid" v-if="marketSentiment && marketSentiment.today">
               <!-- Card 1: Limit Up / Down -->
               <div class="stat-card mixed-bg">
                 <div class="sub-stat">
                   <div class="stat-header-mini">
                      <span class="stat-label">涨停</span>
                      <el-tag size="small" type="danger" effect="dark" class="mini-tag">今</el-tag>
                   </div>
                   <div class="stat-content-mini">
                      <div class="value-row">
                          <span class="stat-value red">{{ marketSentiment.today.limit_up }}</span>
                          <span class="trend-icon" v-if="marketSentiment.yesterday">
                              <el-icon v-if="marketSentiment.today.limit_up > marketSentiment.yesterday.limit_up" class="text-red"><CaretTop /></el-icon>
                              <el-icon v-else-if="marketSentiment.today.limit_up < marketSentiment.yesterday.limit_up" class="text-green"><CaretBottom /></el-icon>
                          </span>
                      </div>
                      <span class="stat-sub-val">昨: {{ marketSentiment.yesterday?.limit_up || '-' }}</span>
                   </div>
                 </div>
                 <div class="divider-vertical"></div>
                 <div class="sub-stat">
                   <div class="stat-header-mini">
                      <span class="stat-label">跌停</span>
                      <el-tag size="small" type="success" effect="dark" class="mini-tag">今</el-tag>
                   </div>
                   <div class="stat-content-mini">
                      <div class="value-row">
                          <span class="stat-value green">{{ marketSentiment.today.limit_down }}</span>
                          <span class="trend-icon" v-if="marketSentiment.yesterday">
                              <el-icon v-if="marketSentiment.today.limit_down > marketSentiment.yesterday.limit_down" class="text-green"><CaretTop /></el-icon>
                              <el-icon v-else-if="marketSentiment.today.limit_down < marketSentiment.yesterday.limit_down" class="text-red"><CaretBottom /></el-icon>
                          </span>
                      </div>
                      <span class="stat-sub-val">昨: {{ marketSentiment.yesterday?.limit_down || '-' }}</span>
                   </div>
                 </div>
               </div>

               <!-- Card 2: Rise / Fall -->
               <div class="stat-card mixed-bg">
                 <div class="sub-stat">
                   <div class="stat-header-mini">
                      <span class="stat-label">上涨</span>
                   </div>
                   <div class="stat-content-mini">
                      <div class="value-row">
                          <span class="stat-value red">{{ marketSentiment.today.rise }}</span>
                          <span class="trend-icon" v-if="marketSentiment.yesterday">
                              <el-icon v-if="marketSentiment.today.rise > marketSentiment.yesterday.rise" class="text-red"><CaretTop /></el-icon>
                              <el-icon v-else-if="marketSentiment.today.rise < marketSentiment.yesterday.rise" class="text-green"><CaretBottom /></el-icon>
                          </span>
                      </div>
                      <span class="stat-sub-val">昨: {{ marketSentiment.yesterday?.rise || '-' }}</span>
                   </div>
                 </div>
                 <div class="divider-vertical"></div>
                 <div class="sub-stat">
                   <div class="stat-header-mini">
                      <span class="stat-label">下跌</span>
                   </div>
                   <div class="stat-content-mini">
                      <div class="value-row">
                          <span class="stat-value green">{{ marketSentiment.today.fall }}</span>
                          <span class="trend-icon" v-if="marketSentiment.yesterday">
                              <el-icon v-if="marketSentiment.today.fall > marketSentiment.yesterday.fall" class="text-green"><CaretTop /></el-icon>
                              <el-icon v-else-if="marketSentiment.today.fall < marketSentiment.yesterday.fall" class="text-red"><CaretBottom /></el-icon>
                          </span>
                      </div>
                      <span class="stat-sub-val">昨: {{ marketSentiment.yesterday?.fall || '-' }}</span>
                   </div>
                 </div>
               </div>

               <!-- Card 3: Volume -->
               <div class="stat-card vol-bg single-col">
                 <div class="stat-header-mini center">
                    <span class="stat-label">量能 (9:25)</span>
                 </div>
                 <div class="stat-content-mini center">
                    <div class="value-row">
                        <span class="stat-value blue">{{ formatAmount(marketSentiment.today.volume) }}</span>
                        <span class="trend-icon" v-if="marketSentiment.yesterday">
                            <el-icon v-if="marketSentiment.today.volume > marketSentiment.yesterday.volume" class="text-red"><CaretTop /></el-icon>
                            <el-icon v-else-if="marketSentiment.today.volume < marketSentiment.yesterday.volume" class="text-green"><CaretBottom /></el-icon>
                        </span>
                    </div>
                    <span class="stat-sub-val">昨: {{ formatAmount(marketSentiment.yesterday?.volume) }}</span>
                 </div>
               </div>
            </div>
            <div v-else class="no-data">暂无数据</div>
          </el-card>

          <!-- 2. One Word Board -->
          <el-card class="box-card" :body-style="{ padding: '0px' }" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
            <template #header>
              <div class="card-header">
                <span>一字板 (9:25 涨幅10%)</span>
              </div>
            </template>
            <el-table :data="limitUp925List" style="width: 100%; flex: 1;" height="100%" stripe :header-cell-style="{background:'#f5f7fa'}">
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
                <el-table-column prop="amount" label="封单额" width="100">
                <template #default="scope">
                    {{ formatAmount(scope.row.amount) }}
                </template>
                </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import axios from 'axios'
import { CaretTop, CaretBottom, Refresh } from '@element-plus/icons-vue'

const topNList = ref([])
const ranking920List = ref([])
const ranking915List = ref([])
const yesterdayLimitUpList = ref([])
const limitUp925List = ref([])
const marketSentiment = ref(null)
const autoRefresh = ref(true)
const refreshInterval = ref(5000)

// Refs for scroll synchronization
const rankListRef = ref(null)
const mainListRef = ref(null)
const subList920Ref = ref(null)
const subList915Ref = ref(null)

// Hover state
const hoveredCode = ref(null)

const handleMouseEnter = (code) => {
  hoveredCode.value = code
}

const handleMouseLeave = () => {
  hoveredCode.value = null
}

const scrollLock = ref(null)
const scrollLockTimer = ref(null)

const handleScroll = (region) => {
  if (scrollLock.value && scrollLock.value !== region) return
  
  // Acquire lock
  scrollLock.value = region
  clearTimeout(scrollLockTimer.value)
  scrollLockTimer.value = setTimeout(() => {
    scrollLock.value = null
  }, 100) // 100ms release time

  const refs = {
    rank: rankListRef.value,
    main: mainListRef.value,
    sub920: subList920Ref.value,
    sub915: subList915Ref.value
  }
  
  const source = refs[region]
  if (!source) return
  
  const maxScroll = source.scrollHeight - source.clientHeight
  if (maxScroll <= 0) return
  
  const percentage = source.scrollTop / maxScroll
  
  Object.keys(refs).forEach(key => {
    if (key !== region) {
      const target = refs[key]
      if (target) {
        const targetMax = target.scrollHeight - target.clientHeight
        if (targetMax > 0) {
           target.scrollTop = percentage * targetMax
        }
      }
    }
  })
}

// Computed property for grouping yesterday limit up data
const groupedYesterdayLimitUp = computed(() => {
  if (!yesterdayLimitUpList.value || yesterdayLimitUpList.value.length === 0) return []
  
  const fanbaoItems = []
  const regularGroups = {}
  
  yesterdayLimitUpList.value.forEach(item => {
    const days = item.consecutive_days || 0  // 几天几板中的连续几天
    const boards = item.consecutive_boards || 0 // 连扳数
    const edition = item.edition || 0 // 几天几板，不一定连扳
    
    // Counter-package condition: consecutive_days > 4 AND consecutive_boards < 3
    if (days > 4 && boards < 3) {
      fanbaoItems.push(item)
    } else {
      // Regular grouping
      if (!regularGroups[boards]) {
        regularGroups[boards] = []
      }
      regularGroups[boards].push(item)
    }
  })
  
  // Sort regular groups
  const sortedRegular = Object.keys(regularGroups)
    .map(key => parseInt(key))
    .sort((a, b) => b - a) // Descending
    .map(boards => {
      const items = regularGroups[boards]
      
      // Calculate limit up count (approximate based on opening price change)
      const limitUpCount = items.filter(item => {
        if (!item.change_percent) return false
        const change = parseFloat(item.change_percent)
        const name = item.name || ''
        const code = item.code || ''
        
        let threshold = 9.8
        if (name.includes('ST')) {
          threshold = 4.8
        } else if (code.startsWith('300') || code.startsWith('688')) {
          threshold = 19.8
        } else if (code.startsWith('8') || code.startsWith('43') || code.startsWith('83') || code.startsWith('87')) {
          threshold = 29.8
        }
        
        return change >= threshold
      }).length
      
      const total = items.length
      const rate = total > 0 ? Math.round((limitUpCount / total) * 100) : 0
      
      return {
        key: `boards-${boards}`,
        label: `${boards}进${boards + 1}板 晋级率：${limitUpCount}/${total}=${rate}%`,
        items: items,
        rate: rate
      }
    })
    
  // Prepend fanbao group if exists
  if (fanbaoItems.length > 0) {
    // Sort fanbao items by days descending
    fanbaoItems.sort((a, b) => (b.consecutive_days || 0) - (a.consecutive_days || 0))
    
    return [
      {
        key: 'fanbao',
        label: '高位反包',
        items: fanbaoItems
      },
      ...sortedRegular
    ]
  }
  
  return sortedRegular
})

const splitSector = (sectorStr) => {
  if (!sectorStr) return []
  // Split by common delimiters: space, comma, semicolon, enumeration comma (English or Chinese)
  // Filter out empty strings
  return sectorStr.split(/[\s,;；、]+/).filter(s => s && s.trim().length > 0)
}

const yesterdayLimitUpMap = computed(() => {
  const map = {}
  if (yesterdayLimitUpList.value) {
    yesterdayLimitUpList.value.forEach(item => {
      map[item.code] = item
    })
  }
  return map
})

const processedTopNList = computed(() => {
  if (!topNList.value) return []
  return topNList.value.map(item => {
    const yesterdayItem = yesterdayLimitUpMap.value[item.code]
    if (yesterdayItem && yesterdayItem.sector) {
      // Create a shallow copy to avoid mutating the original item and to trigger reactivity
      return { ...item, sector: yesterdayItem.sector }
    }
    return item
  })
})

// Compute frequency of each sector in the Top N list
const sectorFrequency = computed(() => {
  const freq = {}
  if (!processedTopNList.value) return freq
  
  processedTopNList.value.forEach(item => {
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

const getRankClass = (index) => {
  if (index === 0) return 'rank-top-1'
  if (index === 1) return 'rank-top-2'
  if (index === 2) return 'rank-top-3'
  if (index < 10) return 'rank-top-10'
  return ''
}

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

// Compute frequency of each sector in the Yesterday Limit Up list
const yesterdayLimitUpSectorFrequency = computed(() => {
  const freq = {}
  if (!yesterdayLimitUpList.value) return freq
  
  yesterdayLimitUpList.value.forEach(item => {
    if (!item.sector) return
    const sectors = splitSector(item.sector)
    sectors.forEach(sec => {
      freq[sec] = (freq[sec] || 0) + 1
    })
  })
  return freq
})

const getSortedLimitUpSectors = (sectorStr) => {
  const sectors = splitSector(sectorStr)
  return sectors.sort((a, b) => {
    const countA = yesterdayLimitUpSectorFrequency.value[a] || 0
    const countB = yesterdayLimitUpSectorFrequency.value[b] || 0
    return countB - countA // Descending
  })
}

const getLimitUpHeatStyle = (sectorName) => {
  const count = yesterdayLimitUpSectorFrequency.value[sectorName] || 0
  
  // Logic:
  // 1. High absolute count (>=3) -> Solid, Bold Color (Hash-based Hue)
  // 2. Medium absolute count (2) -> Light Background, Colored Text (Hash-based Hue)
  // 3. Low absolute count (1) -> Grey (Noise reduction)
  
  if (count <= 1) {
      return { backgroundColor: '#f4f4f5', color: '#909399', border: '1px solid #e9e9eb' } // Single (Gray)
  }

  // Generate distinct color based on name hash to ensure same sector has same color
  let hash = 0
  for (let i = 0; i < sectorName.length; i++) {
    hash = sectorName.charCodeAt(i) + ((hash << 5) - hash)
  }
  
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
          border: 'none',
          fontWeight: 'bold'
      }
  } else {
      // Medium Heat (count == 2): Light Background, Colored Text
      return { 
          backgroundColor: colorSet.light, 
          color: colorSet.text, 
          border: `1px solid ${colorSet.border}`
      }
  }
}

const rank915Map = computed(() => {
  const map = {}
  if (ranking915List.value) {
    ranking915List.value.forEach((item, index) => {
      map[item.code] = index
    })
  }
  return map
})

const getRankChangeInfo = (code, currentRank) => {
  const rank915 = rank915Map.value[code]
  
  if (rank915 === undefined) return null
  
  // currentRank is 0-based. Lower index = Higher rank.
  const diff = rank915 - currentRank
  
  if (diff > 0) {
    // Rank improved (e.g., 2 < 5, diff = 3) -> Red Up
    return { icon: CaretTop, color: '#f56c6c', text: `+${diff}` }
  } else if (diff < 0) {
    // Rank declined (e.g., 5 > 2, diff = -3) -> Green Down
    return { icon: CaretBottom, color: '#67c23a', text: `${diff}` }
  }
  
  return null
}

const limitUp925Set = computed(() => {
  const set = new Set()
  if (limitUp925List.value) {
    limitUp925List.value.forEach(item => set.add(item.code))
  }
  return set
})

const getBoardTagInfo = (item) => {
   // Check if currently limit up (at 9:25)
   // Rely strictly on limitUp925Set for 9:25 limit up status as requested by user.
   // Fallback logic is removed to avoid incorrect "First Board" labeling for non-limit-up stocks.
   const isLimitUp = limitUp925Set.value.has(item.code)
   
   const prevDays = item.consecutive_days || 0
   
   const prevBoards = item.consecutive_boards || 0
  
  if (isLimitUp) {
    if (prevDays === 0) {
      return { text: '首板', class: 'board-tag' }
    } else {
      if (prevDays == prevBoards) {
        return { text: (prevBoards + 1) + '板', class: 'board-tag' }
      } else {
        return { text: (prevDays + 1) + '天' + (prevBoards + 1) + '板', class: 'board-tag' }
      }
    }
  } else {
    // Not limit up now
    if (prevDays == 1 && prevBoards == 1) {
      return { text: '昨首板', class: 'broken-board-tag' }
    }
    if (prevDays > 1) {
      if (prevDays == prevBoards) {
        return { text: '昨' + prevBoards + '板', class: 'broken-board-tag' }
      } else {
        return { text: '昨' + prevDays + '天' + prevBoards + '板', class: 'broken-board-tag' }
      }
    }
  }
  
  return null
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
      fetchMarketSentiment()
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

const fetchMarketSentiment = async () => {
  try {
    const response = await axios.get('/api/market/sentiment_925', {
      params: { 
        date: selectedDate.value,
        _t: new Date().getTime() // Prevent caching
      }
    })
    marketSentiment.value = response.data
  } catch (error) {
    console.error('Error fetching market sentiment:', error)
  }
}

const refreshAll = () => {
  fetchTopN()
  fetchYesterdayLimitUp()
  fetchLimitUp925()
  fetchMarketSentiment()
}

const handleDateChange = () => {
  refreshAll()
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

  refreshAll()
  
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

/* Hide scrollbar for Chrome, Safari and Opera */
.main-list::-webkit-scrollbar,
.sub-list::-webkit-scrollbar,
.yesterday-limit-up-container::-webkit-scrollbar {
  display: none;
}

/* Hide scrollbar for IE, Edge and Firefox */
.main-list,
.sub-list,
.yesterday-limit-up-container {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
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
  position: relative;
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 6px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  transition: all 0.2s;
  font-weight: 600;
  height: 60px; /* Fixed height for consistency */
  box-sizing: border-box;
}
.rank-change-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  height: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}
.rank-change-text {
  font-size: 12px;
  margin-right: 2px;
}
.top-n-card:hover,
.top-n-card.is-hovered {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #e6a23c;
  background-color: #fdf6ec;
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
.broken-board-tag {
  background-color: #f4f4f5;
  color: #909399;
  border: 1px solid #e9e9eb;
}
.top-n-body {
  display: flex;
  align-items: center;
  font-size: 13px; /* Reduced from 14px */
  color: #606266;
  white-space: nowrap; /* Prevent wrapping */
  overflow: hidden; /* Hide overflow */
}
.amount-val {
  font-family: monospace;
  font-weight: bold;
  font-size: 13px; /* Reduced from 15px */
}
.amount-925 {
  color: #e6a23c; /* Orange/Gold */
  font-size: 14px; /* Reduced from 16px, still slightly larger */
}
.amount-920 {
  color: #409eff; /* Blue */
}
.amount-915 {
  color: #f56c6c; /* Red */
}
.separator {
  margin: 0 4px; /* Reduced from 8px */
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
  margin-bottom: 12px;
  color: #303133;
  padding: 8px 12px;
  background-color: #ecf5ff;
  border-radius: 4px;
  border-left: 5px solid #409eff;
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
  padding: 12px 16px;
  margin: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  background-color: #fafafa;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  transition: all 0.2s;
  flex-grow: 0;
  position: relative;
}

.stock-card .stock-name {
  font-size: 15px;
  font-weight: bold; /* Ensure bold is kept/added if needed, though .stock-name has it */
}

.stock-card .stock-info {
  font-size: 16px;
  font-weight: bold;
}

.stock-card .stock-tag {
  font-size: 14px;
}

.edition-badge {
  position: absolute;
  top: -10px;
  right: -10px;
  background-color: #e6a23c;
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  white-space: nowrap;
  z-index: 10;
  font-weight: bold;
}

.limit-up-20cm-badge {
  position: absolute;
  top: -10px;
  left: -10px;
  background-color: #f56c6c;
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  white-space: nowrap;
  z-index: 10;
  font-weight: bold;
}

.stock-card:hover,
.stock-card.is-hovered {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #e6a23c;
  background-color: #fdf6ec;
}

/* Rank Card */
.rank-card {
  height: 60px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #ebeef5;
  background-color: #fff;
  margin-bottom: 6px;
  transition: all 0.2s;
}

.rank-card.is-hovered {
  background-color: #fdf6ec;
  border-color: #e6a23c;
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
  z-index: 1;
  position: relative;
}

.rank-number {
    font-size: 14px;
    font-weight: bold;
    color: #909399;
    width: 24px;
    height: 24px;
    line-height: 24px;
    text-align: center;
    border-radius: 4px;
}

/* Market Sentiment Grid */
.sentiment-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.stat-card {
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  transition: all 0.2s;
  min-height: 60px;
  background: #fff;
  border: 1px solid #ebeef5;
}

.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stat-card.single-col {
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.sub-stat {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.divider-vertical {
    width: 1px;
    height: 40px;
    background-color: #ebeef5;
    margin: 0 10px;
}

/* Background Colors */
.mixed-bg {
  background: linear-gradient(to right, #fff, #fdfdfd);
}

.vol-bg {
  background: linear-gradient(135deg, #ecf5ff 0%, #ffffff 100%);
  border: 1px solid #d9ecff;
}

/* Content Styles */
.stat-header-mini {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2px;
  width: 100%;
}

.stat-header-mini.center {
    justify-content: center;
}

.stat-label {
  font-size: 16px;
  color: #606266;
  font-weight: bold;
  margin-right: 4px;
}

.mini-tag {
    transform: scale(0.8);
    transform-origin: left center;
    margin-left: -2px;
}

.stat-content-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-content-mini.center {
    align-items: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
}

.stat-value.red { color: #f56c6c; }
.stat-value.green { color: #67c23a; }
.stat-value.blue { color: #409eff; }

.stat-sub-val {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
  white-space: nowrap;
}

.rank-number.rank-top-1 {
    color: #fff;
    background-color: #f56c6c;
  }
  
  .rank-number.rank-top-2 {
    color: #fff;
    background-color: #e6a23c;
  }
  
  .rank-number.rank-top-3 {
    color: #fff;
    background-color: #faad14;
  }
  
  .rank-number.rank-top-10 {
    color: #303133;
    font-weight: 900;
    font-size: 16px;
  }

/* 9:20 and 9:15 Card Style */
.mini-card {
  padding: 6px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 6px; /* Match top-n-card margin-bottom */
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.2s;
  font-size: 15px;
  font-weight: 600;
  height: 60px; /* Match top-n-card height */
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mini-card:hover,
.mini-card.is-hovered {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #e6a23c;
  background-color: #fdf6ec;
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

/* Trend Icon */
.value-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
}

.trend-icon {
    display: flex;
    align-items: center;
    font-size: 20px;
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