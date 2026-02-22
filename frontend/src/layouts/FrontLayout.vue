<template>
  <div class="front-layout">
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
import { store, disabledDate } from '../store/dashboard.js'
</script>

<style scoped>
.front-layout {
  min-height: 100vh;
  background-color: #f0f2f5;
}
.front-header {
  background-color: #1e1e1e; /* Dark theme background */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
  height: 56px;
  color: #fff;
  border-bottom: 2px solid #cf1322; /* Red accent line */
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
    color: #cf1322; /* China Red */
    letter-spacing: 1px;
}
.logo-text-title {
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    margin-left: 4px;
}
.logo-tag {
    background: #cf1322;
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
    color: #a0a0a0;
}
.divider {
    width: 1px;
    height: 18px;
    background-color: #3a3a3a;
    margin: 0 5px;
}

/* Override Element Plus Styles for Dark Header */
:deep(.el-input__wrapper) {
    background-color: #2b2b2b;
    box-shadow: 0 0 0 1px #3a3a3a inset;
}
:deep(.el-input__wrapper:hover) {
    box-shadow: 0 0 0 1px #cf1322 inset;
}
:deep(.el-input__inner) {
    color: #fff;
    font-weight: 500;
}
:deep(.el-date-editor .el-icon) {
    color: #a0a0a0;
}
:deep(.el-switch__core) {
    border-color: #4a4a4a;
    background-color: #4a4a4a;
}
:deep(.el-switch.is-checked .el-switch__core) {
    border-color: #13ce66;
    background-color: #13ce66;
}
</style>