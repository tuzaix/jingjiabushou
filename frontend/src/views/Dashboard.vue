<template>
  <div class="dashboard-container">
    <el-row :gutter="4">
      <!-- 1. Ranking Monitor (Left) -->
      <el-col :span="7">
          <el-card class="box-card full-height-card card-body-flex">
          <template #header>
            <div class="card-header">
              <span>竞价排名监控 (9:15 / 9:20 / 9:25)</span>
            </div>
          </template>
          <div class="monitor-container">
             <!-- Rank Column -->
             <div class="rank-column">
                <div class="list-header-title text-secondary">序号</div>
                <div class="rank-list sub-list scrollable-list" ref="rankListRef" @scroll="handleScroll('rank')">
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
             <div class="main-column">
                <div class="list-header-title text-gold">9:25 排名</div>
                <div class="main-list scrollable-list" ref="mainListRef" @scroll="handleScroll('main')">
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
            <div class="sub-column">
               <div class="list-header-title text-blue">9:20 排名</div>
               <div class="sub-list scrollable-list" ref="subList920Ref" @scroll="handleScroll('sub920')">
                  <div v-for="(item, index) in ranking920List" :key="item.code" 
                        class="mini-card"
                        :class="{ 'is-hovered': hoveredCode === item.code }"
                        @mouseenter="handleMouseEnter(item.code)" 
                        @mouseleave="handleMouseLeave">
                     <div class="flex-column-center-full">
                        <div class="mini-row mb-2">
                            <span class="mini-name">{{ item.name }}</span>
                        </div>
                        <div class="mini-row mb-0">
                            <span class="stock-info amount font-12-m0">{{ formatAmount(item.amount) }}</span>
                            <span v-if="item.change_percent !== undefined" :class="getChangeClass(item.change_percent)" class="stock-info amount font-12-m0 ml-10">{{ formatChange(item.change_percent) }}</span>
                        </div>
                     </div>
                  </div>
                  <div v-if="ranking920List.length === 0" class="no-data">暂无数据</div>
               </div>
            </div>

            <!-- 9:15 List -->
            <div class="sub-column-last">
               <div class="list-header-title text-red">9:15 排名</div>
               <div class="sub-list scrollable-list" ref="subList915Ref" @scroll="handleScroll('sub915')">
                   <div v-for="(item, index) in ranking915List" :key="item.code" 
                         class="mini-card"
                         :class="{ 'is-hovered': hoveredCode === item.code }"
                         @mouseenter="handleMouseEnter(item.code)" 
                         @mouseleave="handleMouseLeave">
                      <div class="flex-column-center-full">
                         <div class="mini-row mb-2">
                             <span class="mini-name">{{ item.name }}</span>
                         </div>
                         <div class="mini-row mb-0">
                             <span class="stock-info amount font-12-m0">{{ formatAmount(item.amount) }}</span>
                             <span v-if="item.change_percent !== undefined" :class="getChangeClass(item.change_percent)" class="stock-info amount font-12-m0 ml-10">{{ formatChange(item.change_percent) }}</span>
                         </div>
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
          <el-card class="box-card full-height-card card-body-flex">
            <template #header>
              <div class="card-header">
                <span>昨日涨停表现 (9:25)</span>
              </div>
            </template>
            <div class="yesterday-limit-up-container scrollable-list">
               <div v-for="group in groupedYesterdayLimitUp" :key="group.key" class="limit-up-group">
                 <div class="group-label">
                    {{ group.label }}
                    <el-tag v-if="group.rate >= 50" type="danger" effect="dark" size="small" class="ml-10">强</el-tag>
                    <el-tag v-else-if="group.rate < 20" type="info" effect="dark" size="small" class="ml-10">弱</el-tag>
                 </div>
                 <div class="group-items">
                    <div v-for="item in group.items" :key="item.code" 
                         class="stock-card"
                         :class="{ 'is-hovered': hoveredCode === item.code }"
                         @mouseenter="handleMouseEnter(item.code)" 
                         @mouseleave="handleMouseLeave">
                         
                       <div v-if="item.is_20cm" class="circle-20cm" title="20cm">20%</div>
                       <div v-if="item.edition && item.edition > 1 && item.edition !== item.consecutive_boards" class="edition-badge">{{ item.consecutive_days }}天{{ item.edition }}板</div>
                       
                       <div class="flex-column-full">
                           <div class="flex-between-center-mb4">
                               <div class="flex-center-gap4">
                                 <span class="stock-name">{{ item.name }}</span>
                               </div>
                               <span class="stock-info" :class="getChangeClass(item.change_percent)">{{ formatChange(item.change_percent) }}</span>
                           </div>
                           <div class="flex-between-center">
                               <span class="stock-info amount">
                                 {{ formatAmount(item.bidding_amount) }}
                                 <template v-if="(!item.is_20cm && item.change_percent >= 9.8 && item.asking_amount > 0) || (item.is_20cm && item.change_percent >= 19.8 && item.asking_amount > 0)">
                                   / {{ formatAmount(item.asking_amount) }}
                                 </template>
                               </span>
                               <span v-for="sec in getSortedSectors(item.sector).slice(0, 1)" :key="sec" class="stock-tag" :style="getHeatStyle(sec)">{{ sec }}</span>
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
        <div class="right-side-container">
          <!-- 3.1 Market Sentiment -->
          <el-card class="box-card card-body-p15 flex-none">
            <template #header>
              <div class="card-header">
                <span>大局观 (9:25)</span>
              </div>
            </template>
            <!-- Index Data Card -->
            <div v-if="indexData && indexData.length > 0" class="index-overview-row">
                <div v-for="idx in indexData" :key="idx.index_code" class="stat-card index-stat-card">
                    <div class="index-stat-content">
                        <span class="index-stat-label">{{ idx.index_name }}</span>
                        <span :class="getChangeClass(idx.increase_rate)" class="index-stat-value">{{ formatIndexRate(idx.increase_rate) }}</span>
                        <span :class="getChangeClass(idx.increase_rate)" class="index-stat-value">{{ idx.index_volume }}</span>
                        <span :class="getChangeClass(idx.increase_rate)" class="index-stat-amount">{{ formatIndexAmount(idx.increase_amount) }}</span>
                    </div>
                </div>
            </div>
            <div v-else class="no-data-mini">暂无指数数据</div>

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

          <div class="bottom-row-container">
            <!-- 3.2 One Word Board -->
            <el-card class="box-card flex-card card-body-flex">
            <template #header>
              <div class="card-header">
                <span>一字板</span>
              </div>
            </template>
            <div class="card-list-container">
                <div v-for="item in limitUp925List" :key="item.code" class="list-card" @mouseenter="handleMouseEnter(item.code)" @mouseleave="handleMouseLeave" :class="{ 'is-hovered': hoveredCode === item.code }">
                    <div class="list-card-row">
                        <span class="list-card-name">{{ item.name }}</span>
                        <span class="text-red bold-percent">{{ item.change_percent }}%</span>
                    </div>
                    <div class="list-card-row">
                        <span class="list-card-amount">封单: {{ formatAmount(item.amount) }}</span>
                        <span v-for="sec in getSortedSectors(item.sector).slice(0, 1)" :key="sec" class="stock-tag" :style="getHeatStyle(sec)">{{ sec }}</span>
                    </div>
                </div>
            </div>
          </el-card>

          <!-- 3.3 Abnormal Movement -->
          <el-card class="box-card flex-card card-body-flex">
            <template #header>
              <div class="card-header">
                <span>弱转强</span>
              </div>
            </template>
            <div class="card-list-container">
                <div v-for="item in abnormalMovement925List" :key="item.code" class="list-card" @mouseenter="handleMouseEnter(item.code)" @mouseleave="handleMouseLeave" :class="{ 'is-hovered': hoveredCode === item.code }">
                    <div class="list-card-row">
                        <span class="list-card-name">{{ item.name }}</span>
                        <div class="abnormal-movement-info">
                            <span :class="getChangeClass(item.amplitude)" class="amplitude-val">拉:{{ formatPercent(item.amplitude) }}%</span>
                            <span :class="getChangeClass(item.change_percent)" class="bold-percent">{{ item.change_percent }}%</span>
                        </div>
                    </div>
                    <div class="list-card-row">
                        <span class="list-card-amount">成交: {{ formatAmount(item.amount) }}</span>
                        <span v-for="sec in getSortedSectors(item.sector).slice(0, 1)" :key="sec" class="stock-tag" :style="getHeatStyle(sec)">{{ sec }}</span>
                    </div>
                </div>
            </div>
          </el-card>

          <!-- 3.4 Nuclear Button (Limit Down) -->
          <el-card class="box-card flex-card card-body-flex">
            <template #header>
              <div class="card-header">
                <span>核按钮</span>
              </div>
            </template>
            <div class="card-list-container">
                <div v-for="item in limitDown925List" :key="item.code" class="list-card" @mouseenter="handleMouseEnter(item.code)" @mouseleave="handleMouseLeave" :class="{ 'is-hovered': hoveredCode === item.code }">
                    <div class="list-card-row">
                        <span class="list-card-name">{{ item.name }}</span>
                        <span class="text-green bold-percent">{{ item.change_percent }}%</span>
                    </div>
                    <div class="list-card-row">
                        <span class="list-card-amount">封单: {{ formatAmount(item.amount) }}</span>
                        <span v-for="sec in getSortedSectors(item.sector).slice(0, 1)" :key="sec" class="stock-tag" :style="getHeatStyle(sec)">{{ sec }}</span>
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
import { CaretTop, CaretBottom } from '@element-plus/icons-vue'
import { store } from '../store/dashboard.js'

// --- Constants ---
const SECTOR_COLOR_PALETTE = [
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
  { solid: '#be123c', light: '#fff1f2', text: '#be123c', border: '#ffe4e6' }, // Rose-Dark
  { solid: '#0ea5e9', light: '#f0f9ff', text: '#0ea5e9', border: '#e0f2fe' }, // Sky
  { solid: '#10b981', light: '#ecfdf5', text: '#10b981', border: '#d1fae5' }, // Emerald-2
  { solid: '#f59e0b', light: '#fffbeb', text: '#f59e0b', border: '#fef3c7' }, // Amber
  { solid: '#6366f1', light: '#eef2ff', text: '#6366f1', border: '#e0e7ff' }, // Indigo-2
  { solid: '#8b5cf6', light: '#f5f3ff', text: '#8b5cf6', border: '#ede9fe' }, // Violet
  { solid: '#ec4899', light: '#fdf2f8', text: '#ec4899', border: '#fce7f3' }, // Pink-2
  { solid: '#f43f5e', light: '#fff1f2', text: '#f43f5e', border: '#ffe4e6' }, // Rose-2
  { solid: '#14b8a6', light: '#f0fdfa', text: '#14b8a6', border: '#ccfbf1' }, // Teal
  { solid: '#f97316', light: '#fff7ed', text: '#f97316', border: '#ffedd5' }, // Orange-2
  { solid: '#84cc16', light: '#f7fee7', text: '#84cc16', border: '#ecfccb' }, // Lime
  { solid: '#a855f7', light: '#faf5ff', text: '#a855f7', border: '#f3e8ff' }, // Purple-2
  { solid: '#ef4444', light: '#fef2f2', text: '#ef4444', border: '#fee2e2' }  // Red-2
]

// --- State: Data ---
const topNList = ref([])
const ranking920List = ref([])
const ranking915List = ref([])
const yesterdayLimitUpList = ref([])
const limitUp925List = ref([])
const limitDown925List = ref([])
const abnormalMovement925List = ref([])
const marketSentiment = ref(null)
const indexData = ref([])
const isRefreshing = ref(false)

// --- State: Store Integration ---
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

// --- UI Interactivity: Hover & Scroll ---
const hoveredCode = ref(null)
const handleMouseEnter = (code) => { hoveredCode.value = code }
const handleMouseLeave = () => { hoveredCode.value = null }

const rankListRef = ref(null)
const mainListRef = ref(null)
const subList920Ref = ref(null)
const subList915Ref = ref(null)

const scrollLock = ref(null)
const scrollLockTimer = ref(null)

const handleScroll = (region) => {
  if (scrollLock.value && scrollLock.value !== region) return
  
  scrollLock.value = region
  clearTimeout(scrollLockTimer.value)
  scrollLockTimer.value = setTimeout(() => {
    scrollLock.value = null
  }, 100)

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

// --- Business Logic: Computed & Helpers ---
const calculateLimitUpCount = (items) => {
  return items.filter(item => {
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
}

const processYesterdayLimitUpData = (data) => {
  if (!data || data.length === 0) return []
  
  const fanbaoItems = []
  const regularGroups = {}
  
  data.forEach(item => {
    const days = item.consecutive_days || 0
    const boards = item.consecutive_boards || 0
    
    if (days > 4 && boards < 3) {
      fanbaoItems.push(item)
    } else {
      if (!regularGroups[boards]) regularGroups[boards] = []
      regularGroups[boards].push(item)
    }
  })
  
  const sortedRegular = Object.keys(regularGroups)
    .map(key => parseInt(key))
    .sort((a, b) => b - a)
    .map(boards => {
      const items = regularGroups[boards]
      const limitUpCount = calculateLimitUpCount(items)
      const total = items.length
      const rate = total > 0 ? Math.round((limitUpCount / total) * 100) : 0
      
      let label = `${boards}进${boards + 1}板 晋级率：${limitUpCount}/${total}=${rate}%`
      if (boards === 1) {
        label = `1进2板 晋级率：${limitUpCount}/${total}=${rate}%`
      }
      
      return {
        key: `boards-${boards}`,
        label: label,
        items: items,
        rate: rate
      }
    })
    
  if (fanbaoItems.length > 0) {
    fanbaoItems.sort((a, b) => (b.consecutive_days || 0) - (a.consecutive_days || 0))
    return [
      { key: 'fanbao', label: '高位反包', items: fanbaoItems },
      ...sortedRegular
    ]
  }
  
  return sortedRegular
}

const groupedYesterdayLimitUp = computed(() => processYesterdayLimitUpData(yesterdayLimitUpList.value))

const splitSector = (sectorStr) => {
  if (!sectorStr) return []
  return sectorStr.split(/[\s,;；、]+/).filter(s => s && s.trim().length > 0)
}

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

const rank915Map = computed(() => {
  const map = {}
  if (ranking915List.value) {
    ranking915List.value.forEach((item, index) => {
      map[item.code] = index
    })
  }
  return map
})

const limitUp925Set = computed(() => {
  const set = new Set()
  if (limitUp925List.value) {
    limitUp925List.value.forEach(item => set.add(item.code))
  }
  return set
})

// --- UI Helpers: Styling & Formatting ---
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
    return countB - countA
  })
}

const getHeatStyle = (sectorName) => {
  const count = sectorFrequency.value[sectorName] || 0
  if (count <= 1) return { backgroundColor: '#f4f4f5', color: '#909399', border: '1px solid #e9e9eb' }
  
  // Use a more robust hash function for better distribution
  let hash = 0
  for (let i = 0; i < sectorName.length; i++) {
    hash = (hash << 5) - hash + sectorName.charCodeAt(i)
    hash |= 0 // Convert to 32bit integer
  }
  
  // Mix in the length to further differentiate similar strings
  hash ^= sectorName.length * 31
  
  const colorSet = SECTOR_COLOR_PALETTE[Math.abs(hash) % SECTOR_COLOR_PALETTE.length]
  const isHighHeat = count >= 3

  return { 
    backgroundColor: isHighHeat ? colorSet.solid : colorSet.light, 
    color: isHighHeat ? '#ffffff' : colorSet.text, 
    border: `1px solid ${isHighHeat ? colorSet.solid : colorSet.border}`,
    fontWeight: 'bold'
  }
}

const getRankChangeInfo = (code, currentRank) => {
  const rank915 = rank915Map.value[code]
  if (rank915 === undefined) return null
  const diff = rank915 - currentRank
  if (diff > 0) return { icon: CaretTop, color: '#f56c6c', text: `+${diff}` }
  if (diff < 0) return { icon: CaretBottom, color: '#67c23a', text: `${diff}` }
  return null
}

const getBoardTagInfo = (item) => {
  const isLimitUp = limitUp925Set.value.has(item.code)
  const days = item.consecutive_days || 0
  const boards = item.consecutive_boards || 0
  
  if (isLimitUp) {
    if (days === 0) return { text: '首板', class: 'board-tag' }
    const tagText = days === boards ? `${boards + 1}板` : `${days + 1}天${boards + 1}板`
    return { text: tagText, class: 'board-tag' }
  }
  
  if (days > 0) {
    if (days === 1 && boards === 1) return { text: '昨首板', class: 'broken-board-tag' }
    const tagText = days === boards ? `${boards}板` : `${days}天${boards}板`
    return { text: `昨${tagText}`, class: 'broken-board-tag' }
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

const formatIndexRate = (val) => {
  if (val === undefined || val === null || val === '') return '-'
  const num = parseFloat(val)
  if (isNaN(num)) return val
  return num > 0 ? `+${num}%` : `${num}%`
}

const formatIndexAmount = (val) => {
  if (val === undefined || val === null || val === '') return '-'
  const num = parseFloat(val)
  if (isNaN(num)) return val
  return num > 0 ? `+${num}` : `${num}`
}

const formatAmount = (val) => {
  if (!val) return '-'
  const num = parseFloat(val)
  if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  return (num / 10000).toFixed(0) + '万'
}

const formatPercent = (val) => {
  if (val === null || val === undefined) return '0.00'
  const num = Number(val)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

// --- Watchers ---
watch(() => store.selectedDate, () => { refreshAll() })
watch(() => store.autoRefresh, (val) => { handleAutoRefreshChange(val) })
watch(() => store.refreshInterval, () => { handleIntervalChange() })

// --- Data Fetching & Timers ---
let timer = null

const startTimer = () => {
  if (timer) clearInterval(timer)
  if (autoRefresh.value) {
    timer = setInterval(refreshAll, refreshInterval.value)
  }
}

const handleAutoRefreshChange = (val) => {
  if (val) startTimer()
  else if (timer) clearInterval(timer)
}

const handleIntervalChange = () => { startTimer() }

const refreshAll = async () => {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await Promise.allSettled([
      fetchTopN(),
      fetchYesterdayLimitUp(),
      fetchLimitUp925(),
      fetchAbnormalMovement925(),
      fetchLimitDown925(),
      fetchMarketSentiment(),
      fetchIndexData()
    ])
  } finally {
    isRefreshing.value = false
  }
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
        _t: new Date().getTime()
      }
    })
    marketSentiment.value = response.data
  } catch (error) {
    console.error('Error fetching market sentiment:', error)
  }
}

const fetchTopN = async () => {
  try {
    const [resTopN] = await Promise.all([
      axios.get('/api/call_auction/top_n', {
        params: { limit: 50, date: selectedDate.value }
      }),
      fetchRankings()
    ])
    topNList.value = resTopN.data
  } catch (error) {
    console.error('Error fetching top N data:', error)
  }
}

const fetchRankings = async () => {
  try {
    const dateStr = selectedDate.value
    const [res920, res915] = await Promise.all([
      axios.get('/api/call_auction/ranking', {
        params: { start_time: '09:20:00', end_time: '09:21:00', limit: 50, date: dateStr }
      }),
      axios.get('/api/call_auction/ranking', {
        params: { start_time: '09:15:00', end_time: '09:16:00', limit: 50, date: dateStr }
      })
    ])
    ranking920List.value = res920.data
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
      params: { date: selectedDate.value, limit: 10 }
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
    const response = await axios.get('/api/yesterday_limit_up', {
      params: { date: selectedDate.value, mode: 'performance' }
    })
    yesterdayLimitUpList.value = response.data
  } catch (error) {
    console.error('Error fetching yesterday limit up:', error)
  }
}

const getTodayStr = () => {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// --- Lifecycle Hooks ---
onMounted(async () => {
  await fetchTradingDays()
  if (tradingDays.value.size > 0 && !tradingDays.value.has(selectedDate.value)) {
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
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap; /* Prevent wrapping */
  overflow: hidden; /* Hide overflow */
}
.amount-val {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  font-weight: bold;
  font-size: 13px;
}
.amount-925 {
  color: var(--primary-red); /* Changed to red */
  font-size: 14px;
}
.amount-920 {
  color: var(--primary-blue); /* Blue */
}
.amount-915 {
  color: var(--primary-gold); /* Orange/Gold for initial call */
}
.separator {
  margin: 0 4px;
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
  height: 60px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 0 16px;
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
  box-sizing: border-box;
}

.stock-card .stock-name {
  font-size: 15px;
  font-weight: bold; /* Ensure bold is kept/added if needed, though .stock-name has it */
}

.stock-card .stock-info {
  font-size: 16px;
  font-weight: bold;
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

/* Index Data Styles */
.index-overview-row {
  margin-bottom: 8px;
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.index-stat-card {
  flex: 1;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-stat-content {
  display: flex;
  flex-direction: row;
  gap: 15px;
  align-items: center;
  width: 100%;
  justify-content: center;
}

.index-stat-label {
  font-weight: bold;
  font-size: 15px;
  color: var(--text-primary);
  white-space: nowrap;
}

.index-stat-value {
  font-size: 16px;
  font-weight: 800;
  font-family: monospace;
}

.index-stat-amount {
  font-size: 14px;
  font-weight: 600;
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
  font-size: 16px;
  color: var(--text-primary);
}

.list-card-amount {
  font-size: 13px;
  color: var(--text-secondary);
}

.circle-20cm {
  position: absolute;
  top: -5px;
  left: -5px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F56C6C;
  color: white;
  font-size: 10px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  line-height: 1;
  z-index: 10;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
  overflow: hidden;
  white-space: nowrap;
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
.mini-name {
  font-weight: bold;
  color: var(--text-primary);
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

.abnormal-movement-info {
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.amplitude-val {
  font-size: 13px;
  font-weight: 600;
}

.bold-percent {
  font-weight: bold;
  font-size: 16px;
}

.no-data-mini {
  margin-bottom: 8px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
}

/* Card Body Styles */
.card-body-p15 :deep(.el-card__body) {
  padding: 15px !important;
}

.card-body-flex :deep(.el-card__body) {
  padding: 0px !important;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.flex-none {
  flex: 0 0 auto;
}

/* More Utility Classes */
.text-secondary {
  color: var(--text-secondary);
}

.flex-column-center-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.flex-column-full {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.flex-between-center {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flex-between-center-mb4 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.flex-center-gap4 {
  display: flex;
  align-items: center;
  gap: 4px;
}

.mb-2 {
  margin-bottom: 2px !important;
}

.mb-0 {
  margin-bottom: 0 !important;
}

.ml-10 {
  margin-left: 10px !important;
}

.font-12-m0 {
  font-size: 12px !important;
  margin: 0 !important;
}

/* Layout Utilities */
.full-height-card {
  height: calc(100vh - 70px);
  display: flex;
  flex-direction: column;
}

.monitor-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.rank-column {
  flex: 0 0 50px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  height: 100%;
}

.main-column {
  flex: 2;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  padding: 0 10px;
  height: 100%;
}

.sub-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  padding: 0 10px;
  height: 100%;
}

.sub-column-last {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-left: 10px;
  height: 100%;
}

.scrollable-list {
  flex: 1;
  overflow-y: auto;
}

.text-gold { color: var(--primary-gold); }
.text-blue { color: var(--primary-blue); }

.right-side-container {
  height: calc(100vh - 70px);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bottom-row-container {
  flex: 1;
  display: flex;
  gap: 4px;
  min-height: 0;
}

.flex-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
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