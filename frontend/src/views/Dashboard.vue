<template>
  <div class="dashboard-container">
    <el-row :gutter="4">
      <!-- 1. Ranking Monitor (Left) -->
      <el-col :span="7">
          <el-card class="box-card" :body-style="{ padding: '0px', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }" style="height: calc(100vh - 70px); display: flex; flex-direction: column;">
          <template #header>
            <div class="card-header">
              <span>竞价排名监控 (9:15 / 9:20 / 9:25)</span>
            </div>
          </template>
          <div class="monitor-container" style="display: flex; flex: 1; overflow: hidden;">
             <!-- Rank Column -->
             <div style="flex: 0 0 50px; display: flex; flex-direction: column; border-right: 1px solid var(--border-color); height: 100%;">
                <div class="list-header-title" style="color: var(--text-secondary);">序号</div>
                <div class="rank-list sub-list" ref="rankListRef" @scroll="handleScroll('rank')" style="flex: 1; overflow-y: auto;">
                   <div v-for="(item, index) in topNList" :key="'rank-' + index" 
                        class="rank-card"
                        :class="{ 'is-hovered': hoveredCode === item.code }"
                        @mouseenter="handleMouseEnter(item.code)" 
                        @mouseleave="handleMouseLeave">
                      <div class="rank-number" :class="getRankClass(index)">{{ index + 1 }}</div>
                   </div>
                </div>
             </div>

             <!-- 9:25 Main List -->
             <div style="flex: 2; display: flex; flex-direction: column; border-right: 1px solid var(--border-color); padding-right: 10px; padding-left: 10px; height: 100%;">
                <div class="list-header-title" style="color: var(--primary-gold);">9:25 排名</div>
                <div class="main-list" ref="mainListRef" @scroll="handleScroll('main')" style="flex: 1; overflow-y: auto;">
                  <div v-for="(item, index) in topNList" :key="item.code" 
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
                  <div v-if="topNList.length === 0" class="no-data">暂无数据</div>
               </div>
            </div>
            
            <!-- 9:20 List -->
            <div style="flex: 1; display: flex; flex-direction: column; border-right: 1px solid var(--border-color); padding: 0 10px; height: 100%;">
               <div class="list-header-title" style="color: var(--primary-blue);">9:20 排名</div>
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
               <div class="list-header-title" style="color: var(--primary-red);">9:15 排名</div>
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

      <!-- 2. Yesterday Limit Up (Middle) -->
      <el-col :span="7">
          <el-card class="box-card" :body-style="{ padding: '0px', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }" style="height: calc(100vh - 70px); display: flex; flex-direction: column;">
            <template #header>
              <div class="card-header">
                <span>昨日涨停表现 (9:25)</span>
              </div>
            </template>
            <div class="yesterday-limit-up-container" style="flex: 1; overflow-y: auto;">
               <div v-for="group in groupedYesterdayLimitUp" :key="group.key" class="limit-up-group">
                 <div class="group-label">
                    {{ group.label }}
                    <el-tag v-if="group.rate >= 50" type="danger" effect="dark" size="small" style="margin-left: 10px;">强</el-tag>
                    <el-tag v-else-if="group.rate < 20" type="info" effect="dark" size="small" style="margin-left: 10px;">弱</el-tag>
                 </div>
                 <div class="group-items">
                    <div v-for="item in group.items" :key="item.code" 
                         class="stock-card"
                         :class="{ 'is-hovered': hoveredCode === item.code }"
                         @mouseenter="handleMouseEnter(item.code)" 
                         @mouseleave="handleMouseLeave">
                         
                       <div v-if="item.is_20cm" class="limit-up-20cm-badge">20cm</div>
                       <div v-if="item.edition && item.edition > 1 && item.edition !== item.consecutive_boards" class="edition-badge">{{ item.edition }}天{{ item.consecutive_boards }}板</div>
                       
                       <div style="display: flex; flex-direction: column; width: 100%;">
                           <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                               <div style="display: flex; align-items: center; gap: 4px;">
                                 <span class="stock-name">{{ item.name }}</span>
                                 <div v-if="item.is_20cm" class="circle-20cm">20cm</div>
                               </div>
                               <span class="stock-info" :class="getChangeClass(item.change_percent)">{{ formatChange(item.change_percent) }}</span>
                           </div>
                           <div style="display: flex; justify-content: space-between; align-items: center;">
                               <span class="stock-info amount">
                                 {{ formatAmount(item.amount) }}
                                 <template v-if="item.change_percent >= 9.8 && item.bid_amount">
                                   / {{ formatAmount(item.bid_amount) }}
                                 </template>
                               </span>
                               <span class="stock-info" v-if="item.sector" style="max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 10px; color: #666;">{{ item.sector }}</span>
                           </div>
                       </div>
                    </div>
                 </div>
               </div>
               <div v-if="groupedYesterdayLimitUp.length === 0" class="no-data">暂无数据</div>
            </div>
          </el-card>
      </el-col>

      <!-- 3. Right Side (Sentiment + Tables) -->
      <el-col :span="10">
        <div style="height: calc(100vh - 70px); display: flex; flex-direction: column; gap: 4px;">
          <!-- 3.1 Market Sentiment -->
          <el-card class="box-card" :body-style="{ padding: '15px' }" style="flex: 0 0 auto;">
            <template #header>
              <div class="card-header">
                <span>大局观 (9:25)</span>
              </div>
            </template>
            <!-- Index Data Card -->
            <div v-if="indexData && indexData.length > 0" class="market-overview-row" style="margin-bottom: 8px; display: flex; flex-direction: row; gap: 8px;">
                <div v-for="idx in indexData" :key="idx.index_code" class="stat-card single-col" style="flex: 1; padding: 0 10px; display: flex; align-items: center; justify-content: center;">
                    <div class="stat-content-mini center" style="display: flex; flex-direction: row; gap: 10px; align-items: baseline; width: 100%; justify-content: center;">
                        <span class="stat-label" style="font-weight: bold; font-size: 16px; white-space: nowrap;">{{ idx.index_name }}</span>
                        <span :class="getChangeClass(idx.increase_rate)" style="font-size: 16px; font-weight: bold;">{{ idx.increase_rate }}%</span>
                        <span :class="getChangeClass(idx.increase_rate)" class="stat-value" style="font-size: 16px;">{{ idx.index_volume }}</span>
                        <span :class="getChangeClass(idx.increase_rate)" style="font-size: 14px;">{{ idx.increase_amount }}</span>
                    </div>
                </div>
            </div>
            <div v-else class="no-data" style="margin-bottom: 8px; text-align: center; color: #999; font-size: 12px;">暂无指数数据</div>

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
            

          </el-card>

          <div style="flex: 1; display: flex; gap: 4px; min-height: 0;">
            <!-- 3.2 One Word Board -->
            <el-card class="box-card" :body-style="{ padding: '0px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
            <template #header>
              <div class="card-header">
                <span>一字板</span>
              </div>
            </template>
            <div class="card-list-container">
                <div v-for="item in limitUp925List" :key="item.code" class="list-card" @mouseenter="hoveredCode = item.code" @mouseleave="hoveredCode = null" :class="{ 'is-hovered': hoveredCode === item.code }">
                    <div class="list-card-row">
                        <span class="list-card-name">{{ item.name }}</span>
                        <span class="text-red" style="font-weight: bold;">{{ item.change_percent }}%</span>
                    </div>
                    <div class="list-card-row">
                        <span class="list-card-amount">封单: {{ formatAmount(item.amount) }}</span>
                        <span class="list-card-sector" v-if="item.sector">{{ item.sector }}</span>
                    </div>
                </div>
            </div>
          </el-card>

          <!-- 3.3 Abnormal Movement -->
          <el-card class="box-card" :body-style="{ padding: '0px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
            <template #header>
              <div class="card-header">
                <span>异动</span>
              </div>
            </template>
            <div class="card-list-container">
                <div v-for="item in abnormalMovement925List" :key="item.code" class="list-card" @mouseenter="hoveredCode = item.code" @mouseleave="hoveredCode = null" :class="{ 'is-hovered': hoveredCode === item.code }">
                    <div class="list-card-row">
                        <span class="list-card-name">{{ item.name }}</span>
                        <span :class="getChangeClass(item.change_percent)" style="font-weight: bold;">{{ item.change_percent }}%</span>
                    </div>
                    <div class="list-card-row">
                        <span class="list-card-amount">成交: {{ formatAmount(item.amount) }}</span>
                        <span class="list-card-sector" v-if="item.sector">{{ item.sector }}</span>
                    </div>
                </div>
            </div>
          </el-card>

          <!-- 3.4 Nuclear Button (Limit Down) -->
          <el-card class="box-card" :body-style="{ padding: '0px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
            <template #header>
              <div class="card-header">
                <span>核按钮</span>
              </div>
            </template>
            <div class="card-list-container">
                <div v-for="item in limitDown925List" :key="item.code" class="list-card" @mouseenter="hoveredCode = item.code" @mouseleave="hoveredCode = null" :class="{ 'is-hovered': hoveredCode === item.code }">
                    <div class="list-card-row">
                        <span class="list-card-name">{{ item.name }}</span>
                        <span class="text-green" style="font-weight: bold;">{{ item.change_percent }}%</span>
                    </div>
                    <div class="list-card-row">
                        <span class="list-card-amount">封单: {{ formatAmount(item.amount) }}</span>
                        <span class="list-card-sector" v-if="item.sector">{{ item.sector }}</span>
                    </div>
                </div>
            </div>
          </el-card>
          </div>
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
const limitDown925List = ref([])
const abnormalMovement925List = ref([])
const marketSentiment = ref(null)
const indexData = ref([])

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

import { store } from '../store/dashboard.js'

const selectedDate = computed({
  get: () => store.selectedDate,
  set: (val) => store.setSelectedDate(val)
})

const tradingDays = computed({
  get: () => store.tradingDays,
  set: (val) => store.setTradingDays(val)
})

const autoRefresh = computed({
  get: () => store.autoRefresh,
  set: (val) => store.setAutoRefresh(val)
})

const refreshInterval = computed({
  get: () => store.refreshInterval,
  set: (val) => store.setRefreshInterval(val)
})

// Watch store changes
watch(() => store.selectedDate, () => {
  refreshAll()
})

watch(() => store.autoRefresh, (val) => {
  handleAutoRefreshChange(val)
})

watch(() => store.refreshInterval, () => {
  handleIntervalChange()
})

let timer = null

const startTimer = () => {
  if (timer) clearInterval(timer)
  if (autoRefresh.value) {
    timer = setInterval(() => {
      fetchTopN()
      fetchLimitUp925()
      fetchAbnormalMovement925()
      fetchLimitDown925()
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


const getTodayStr = () => {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
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

const fetchAbnormalMovement925 = async () => {
  try {
    const response = await axios.get('/api/call_auction/abnormal_movement_925', {
      params: { 
        date: selectedDate.value,
        limit: 50 
      }
    })
    abnormalMovement925List.value = response.data
  } catch (error) {
    console.error('Error fetching abnormal movement 925:', error)
  }
}

const fetchLimitDown925 = async () => {
  try {
    const response = await axios.get('/api/call_auction/limit_down_925', {
      params: { date: selectedDate.value }
    })
    limitDown925List.value = response.data
  } catch (error) {
    console.error('Error fetching limit down 925:', error)
  }
}

const fetchIndexData = async () => {
    try {
        const res = await axios.get('/api/index/latest', {
            params: { date: selectedDate.value }
        })
        indexData.value = res.data
    } catch (e) {
        console.error('Failed to fetch index data:', e)
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

const refreshAll = () => {
  fetchTopN()
  fetchYesterdayLimitUp()
  fetchLimitUp925()
  fetchAbnormalMovement925()
  fetchLimitDown925()
  fetchMarketSentiment()
  fetchIndexData()
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
  padding: 2px;
}

/* List Header Title Style */
.list-header-title {
  height: 40px;
  line-height: 40px;
  background-color: var(--table-header-bg);
  border-radius: 4px;
  margin-bottom: 10px;
  font-weight: bold;
  text-align: center;
  flex-shrink: 0;
  border: 1px solid var(--border-color);
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
  border-bottom: 2px solid var(--primary-red); /* Red accent line for card headers */
  padding-bottom: 10px;
}

.card-header span {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

/* Top N Card Styles */
.top-n-container {
  padding: 5px;
}
.top-n-card {
  position: relative;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-bottom: 6px;
  background: var(--card-bg);
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
  border-color: var(--hover-border); /* Changed to red accent */
  background-color: var(--hover-bg); /* Light red background */
}
.top-n-header {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.stock-name {
  font-size: 15px;
  font-weight: bold;
  color: var(--text-primary);
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
  background-color: var(--hover-bg);
  color: var(--primary-red);
  border: 1px solid var(--hover-border);
}
.broken-board-tag {
  background-color: var(--bg-color);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}
.top-n-body {
  display: flex;
  align-items: center;
  font-size: 13px; /* Reduced from 14px */
  color: var(--text-secondary);
  white-space: nowrap; /* Prevent wrapping */
  overflow: hidden; /* Hide overflow */
}
.amount-val {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  font-weight: bold;
  font-size: 13px; /* Reduced from 15px */
}
.amount-925 {
  color: var(--primary-red); /* Changed to red */
  font-size: 14px; /* Reduced from 16px, still slightly larger */
}
.amount-920 {
  color: var(--primary-blue); /* Blue */
}
.amount-915 {
  color: var(--primary-gold); /* Orange/Gold for initial call */
}
.separator {
  margin: 0 4px; /* Reduced from 8px */
  color: var(--border-color);
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
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 10px;
}

.group-label {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 12px;
  color: var(--text-primary);
  padding: 8px 12px;
  background-color: var(--hover-bg); /* Light red bg */
  border-radius: 4px;
  border-left: 5px solid var(--primary-red); /* Red accent */
}

.group-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stock-card {
  width: auto;
  min-width: 100px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 12px 16px;
  margin: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  background-color: var(--card-bg);
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
  background-color: var(--primary-gold);
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
  background-color: var(--primary-red);
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
  border-color: var(--hover-border);
  background-color: var(--hover-bg);
}

/* Rank Card */
.rank-card {
  height: 60px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--card-bg);
  margin-bottom: 6px;
  transition: all 0.2s;
}

.rank-card.is-hovered {
  background-color: var(--hover-bg);
  border-color: var(--hover-border);
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
  z-index: 1;
  position: relative;
}

.rank-number {
    font-size: 14px;
    font-weight: bold;
    color: var(--text-secondary);
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
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}

.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-color: var(--hover-border);
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
    background-color: var(--border-color);
    margin: 0 10px;
}

/* Background Colors */
.mixed-bg {
  background: linear-gradient(to right, var(--card-bg), var(--bg-color));
}

/* List Card Styles */
.card-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 0;
}

.list-card {
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
  background: var(--card-bg);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  transition: all 0.2s;
  cursor: pointer;
}

.list-card:last-child {
  margin-bottom: 0;
}

.list-card:hover,
.list-card.is-hovered {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: var(--hover-border);
  background-color: var(--hover-bg);
}

.list-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.list-card-row:last-child {
  margin-bottom: 0;
}

.list-card-name {
  font-weight: bold;
  font-size: 15px;
  color: var(--text-primary);
}

.list-card-amount {
  font-size: 12px;
  color: var(--text-secondary);
}

.list-card-sector {
  font-size: 12px;
  color: var(--text-primary);
  background-color: var(--bg-color);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  max-width: 50%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.limit-up-20cm-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background-color: var(--primary-gold);
  color: white;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 8px;
  transform: scale(0.85);
  z-index: 10;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.circle-20cm {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-gold);
  color: white;
  font-size: 9px;
  width: 24px;
  height: 14px;
  border-radius: 7px;
  margin-left: 2px;
  line-height: 1;
}

/* Table Theme Adaptation */
:deep(.el-table) {
  --el-table-bg-color: var(--card-bg);
  --el-table-tr-bg-color: var(--card-bg);
  --el-table-header-bg-color: var(--table-header-bg);
  --el-table-row-hover-bg-color: var(--hover-bg);
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
  /* Stripe color variable for Element Plus */
  --el-fill-color-lighter: var(--bg-color);
  background-color: var(--card-bg);
}

:deep(.el-table th.el-table__cell) {
    background-color: var(--table-header-bg);
}

:deep(.el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: var(--bg-color);
}

:deep(.el-table tr) {
  background-color: var(--card-bg);
}

.vol-bg {
  background: linear-gradient(135deg, var(--hover-bg) 0%, var(--card-bg) 100%);
  border: 1px solid var(--hover-border);
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
  color: var(--text-secondary);
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

.stat-value.red { color: var(--primary-red); }
.stat-value.green { color: var(--primary-green); }
.stat-value.blue { color: var(--primary-blue); }

.stat-sub-val {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
  white-space: nowrap;
}

.rank-number.rank-top-1 {
    color: #fff;
    background-color: var(--primary-red);
  }
  
  .rank-number.rank-top-2 {
    color: #fff;
    background-color: var(--primary-gold);
  }
  
  .rank-number.rank-top-3 {
    color: #fff;
    background-color: var(--primary-gold);
  }
  
  .rank-number.rank-top-10 {
    color: var(--text-primary);
    font-weight: 900;
    font-size: 16px;
  }

/* 9:20 and 9:15 Card Style */
.mini-card {
  padding: 6px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-bottom: 6px; /* Match top-n-card margin-bottom */
  background: var(--card-bg);
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
  border-color: var(--primary-gold);
  background-color: var(--hover-bg);
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
  background-color: var(--bg-color);
  color: var(--text-secondary);
  border-radius: 50%;
  font-size: 10px;
  margin-right: 6px;
}
.rank-badge.top-3 {
  background-color: var(--text-primary);
  color: var(--card-bg);
}
.mini-name {
  font-weight: bold;
  color: var(--text-primary);
}
.mini-row-amount {
  color: var(--text-secondary);
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
  color: var(--text-secondary);
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
    color: var(--primary-red);
}

.text-green {
    color: var(--primary-green);
}

.no-data {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
}

/* Hide scrollbar for tables with no-scrollbar-table class */
.no-scrollbar-table .el-table__body-wrapper::-webkit-scrollbar {
  width: 0 !important;
  height: 0 !important;
  display: none !important;
}

.no-scrollbar-table .el-table__body-wrapper {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.no-scrollbar-table .el-table__header-wrapper .el-table__header {
   width: 100% !important;
}

.no-scrollbar-table .el-table__body-wrapper .el-table__body {
   width: 100% !important;
}
</style>

<style>
/* Global scrollbar hiding for specific dashboard components */
/* Using non-scoped style to ensure ::-webkit-scrollbar works correctly */

/* Hide scrollbar for Webkit browsers (Chrome, Safari) */
.main-list::-webkit-scrollbar,
.sub-list::-webkit-scrollbar,
.yesterday-limit-up-container::-webkit-scrollbar,
.card-list-container::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  background: transparent !important;
  -webkit-appearance: none !important;
}

/* Hide scrollbar for IE, Edge and Firefox */
.main-list,
.sub-list,
.yesterday-limit-up-container,
.card-list-container {
  -ms-overflow-style: none !important;  /* IE and Edge */
  scrollbar-width: none !important;  /* Firefox */
  overflow-y: scroll; /* Ensure scrollability while hiding bars */
}
</style>