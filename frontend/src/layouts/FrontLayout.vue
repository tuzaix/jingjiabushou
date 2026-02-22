<template>
  <div class="front-layout">
    <el-container>
      <el-header class="front-header">
        <div class="header-content">
          <h1>A股竞价捕手</h1>
          
          <div class="header-controls">
            <el-date-picker
              v-model="store.selectedDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledDate"
              style="width: 140px;"
            />
            
            <div class="refresh-control">
                <el-icon class="refresh-icon"><Refresh /></el-icon>
                <el-switch v-model="store.autoRefresh" />
            </div>

            <el-select
              v-model="store.refreshInterval"
              placeholder="间隔"
              style="width: 60px;"
              :disabled="!store.autoRefresh"
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
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'
import { store, disabledDate } from '../store/dashboard.js'
</script>

<style scoped>
.front-layout {
  min-height: 100vh;
  background-color: #f5f7fa;
}
.front-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  z-index: 10;
  height: 60px;
}
.header-content {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-content h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
  margin-right: 40px;
}
.header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-left: auto;
  margin-right: 20px;
}
.refresh-control {
  display: flex; 
  align-items: center;
}
.refresh-icon {
  font-size: 18px; 
  margin-right: 5px; 
  color: #409EFF;
}
</style>