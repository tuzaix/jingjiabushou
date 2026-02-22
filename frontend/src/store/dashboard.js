import { reactive } from 'vue'

const getTodayStr = () => {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const store = reactive({
  selectedDate: getTodayStr(),
  autoRefresh: true,
  refreshInterval: 5000,
  tradingDays: new Set(),
  theme: 'light', // Default theme: 'light', 'dark', 'eye-care'
  
  setTradingDays(days) {
    this.tradingDays = new Set(days)
  },
  
  setSelectedDate(date) {
    this.selectedDate = date
  },
  
  setAutoRefresh(val) {
    this.autoRefresh = val
  },
  
  setRefreshInterval(val) {
    this.refreshInterval = val
  },

  setTheme(val) {
    this.theme = val
    // Optionally save to localStorage here if persistence is needed across refreshes
    localStorage.setItem('app-theme', val)
  }
})

// Initialize theme from localStorage if available
const savedTheme = localStorage.getItem('app-theme')
if (savedTheme && ['light', 'dark', 'eye-care'].includes(savedTheme)) {
  store.theme = savedTheme
}

export const disabledDate = (time) => {
  // Always disable future dates
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (time.getTime() > today.getTime()) {
      return true
  }

  // If tradingDays are loaded, restrict to those days
  if (store.tradingDays.size > 0) {
    const year = time.getFullYear()
    const month = String(time.getMonth() + 1).padStart(2, '0')
    const day = String(time.getDate()).padStart(2, '0')
    const dateStr = `${year}-${month}-${day}`
    return !store.tradingDays.has(dateStr)
  }
  
  // Fallback: disable weekends
  const day = time.getDay()
  return day === 0 || day === 6
}
