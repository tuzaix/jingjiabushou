<template>
  <div class="front-layout" :class="store.theme">
    <el-container>
      <el-header class="front-header">
        <div class="header-content">
          <div class="logo-area">
             <span class="logo-text-cn">A股</span>
             <span class="logo-text-title">竞价捕手</span>
             <span class="logo-tag">Pro</span>
          </div>
          
          <div class="header-controls">
            <div class="control-group">
                <span class="control-label">交易日:</span>
                <el-date-picker
                v-model="store.selectedDate"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledDate"
                style="width: 140px;"
                size="default"
                :clearable="false"
                />
            </div>
            
            <div class="divider"></div>

            <div class="control-group">
                <span class="control-label">自动刷新:</span>
                <el-switch 
                    v-model="store.autoRefresh" 
                    active-color="#13ce66"
                    inactive-color="#ff4949"
                />
            </div>

            <div class="control-group">
                <el-select
                v-model="store.refreshInterval"
                placeholder="间隔"
                style="width: 75px;"
                :disabled="!store.autoRefresh"
                size="default"
                >
                <el-option label="3秒" :value="3000" />
                <el-option label="5秒" :value="5000" />
                <el-option label="10秒" :value="10000" />
                <el-option label="30秒" :value="30000" />
                <el-option label="60秒" :value="60000" />
                </el-select>
            </div>

            <div class="divider"></div>

            <div class="control-group">
                <el-dropdown trigger="click" @command="handleThemeCommand">
                    <span class="theme-trigger">
                        <el-icon><Brush /></el-icon>
                        <span class="theme-text">{{ themeLabel }}</span>
                        <el-icon class="el-icon--right"><arrow-down /></el-icon>
                    </span>
                    <template #dropdown>
                    <el-dropdown-menu>
                        <el-dropdown-item command="light">🌞 亮色模式</el-dropdown-item>
                        <el-dropdown-item command="dark">🌙 暗色模式</el-dropdown-item>
                        <el-dropdown-item command="eye-care">🌿 护眼模式</el-dropdown-item>
                    </el-dropdown-menu>
                    </template>
                </el-dropdown>
            </div>
          </div>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Brush, ArrowDown } from '@element-plus/icons-vue'
import { store, disabledDate } from '../store/dashboard.js'

const themeLabel = computed(() => {
    switch(store.theme) {
        case 'light': return '亮色'
        case 'dark': return '暗色'
        case 'eye-care': return '护眼'
        default: return '主题'
    }
})

const handleThemeCommand = (command) => {
    store.setTheme(command)
}
</script>

<style>
/* Global Variables Definition */
:root {
    --primary-red: #cf1322;
    --primary-green: #52c41a;
    --primary-blue: #1890ff;
    --primary-gold: #faad14;
    
    /* Fixed Header Styles */
    --header-bg: #1e1e1e;
    --header-text: #fff;
}

/* Light Theme (Default) */
.front-layout.light {
    --bg-color: #f0f2f5;
    --card-bg: #ffffff;
    --text-primary: #303133;
    --text-secondary: #606266;
    --text-placeholder: #a0a0a0;
    --border-color: #ebeef5;
    --hover-bg: #fff1f0;
    --hover-border: #cf1322;
    --divider-color: #3a3a3a;
    --control-label: #a0a0a0;
    --table-header-bg: #f5f7fa;
}

/* Dark Theme */
.front-layout.dark {
    --bg-color: #000000; /* Pure Black Background */
    --card-bg: #1C1C1E; /* Dark Grey Card (iOS Style) */
    --text-primary: #FFFFFF; /* Pure White Text */
    --text-secondary: #B0B0B0; /* Light Grey Text */
    --text-placeholder: #606060;
    --border-color: #38383A; /* Visible Dark Grey Border */
    --hover-bg: #2C2C2E; /* Lighter Grey Hover */
    --hover-border: #cf1322;
    --divider-color: #38383A;
    --control-label: #8E8E93;
    --table-header-bg: #2C2C2E; /* Distinct Header Background */
}

/* Eye-care Theme (Warm/Yellowish) */
.front-layout.eye-care {
    --bg-color: #FAF9DE; /* Light yellowish eye-care color */
    --card-bg: #FFFBF0; /* Very light warm white */
    --text-primary: #2c3e50;
    --text-secondary: #5d4037;
    --text-placeholder: #8d6e63;
    --border-color: #E6DAB2;
    --hover-bg: #FFF3E0;
    --hover-border: #FFB74D;
    --divider-color: #D7CCC8;
    --control-label: #D7CCC8;
    --table-header-bg: #EFE8D0;
}
</style>

<style scoped>
.front-layout {
  min-height: 100vh;
  background-color: var(--bg-color);
  transition: background-color 0.3s ease;
}
.front-header {
  background-color: var(--header-bg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
  height: 56px;
  color: var(--header-text);
  border-bottom: 2px solid var(--primary-red);
  transition: background-color 0.3s ease;
}
.header-content {
  max-width: 100%;
  padding: 0 20px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Logo Styles */
.logo-area {
    display: flex;
    align-items: center;
    font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
    user-select: none;
}
.logo-text-cn {
    font-size: 22px;
    font-weight: 800;
    color: var(--primary-red);
    letter-spacing: 1px;
}
.logo-text-title {
    font-size: 20px;
    font-weight: 700;
    color: var(--header-text);
    margin-left: 4px;
}
.logo-tag {
    background: var(--primary-red);
    color: #fff;
    font-size: 10px;
    padding: 1px 4px;
    border-radius: 2px;
    margin-left: 6px;
    font-weight: bold;
    transform: translateY(-8px);
}

/* Controls Styles */
.header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}
.control-group {
    display: flex;
    align-items: center;
    gap: 8px;
}
.control-label {
    font-size: 13px;
    color: var(--control-label);
}
.divider {
    width: 1px;
    height: 18px;
    background-color: var(--divider-color);
    margin: 0 5px;
}

.theme-trigger {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: var(--header-text);
    font-size: 14px;
    padding: 4px 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
}
.theme-trigger:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
.theme-text {
    margin: 0 4px;
}

/* Override Element Plus Styles for Dark Header */
:deep(.el-input__wrapper) {
    background-color: rgba(255, 255, 255, 0.1); /* Semi-transparent for better blending */
    box-shadow: 0 0 0 1px var(--divider-color) inset;
}
:deep(.el-input__wrapper:hover) {
    box-shadow: 0 0 0 1px var(--primary-red) inset;
}
:deep(.el-input__inner) {
    color: var(--header-text);
    font-weight: 500;
}
:deep(.el-date-editor .el-icon) {
    color: var(--control-label);
}
:deep(.el-switch__core) {
    border-color: #4a4a4a;
    background-color: #4a4a4a;
}
:deep(.el-switch.is-checked .el-switch__core) {
    border-color: #13ce66;
    background-color: #13ce66;
}

/* Global Override for Element Plus Card */
:deep(.el-card) {
    background-color: var(--card-bg);
    border-color: var(--border-color);
    color: var(--text-primary);
    transition: all 0.3s ease;
}
:deep(.el-card__header) {
    border-bottom-color: var(--border-color);
}
:deep(.el-card__body) {
    color: var(--text-primary);
}
</style>