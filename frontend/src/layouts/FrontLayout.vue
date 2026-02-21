<template>
  <div class="front-layout">
    <el-container>
      <el-header class="front-header">
        <div class="header-content">
          <h1>A股竞价捕手</h1>
          <div class="nav-links">
            <router-link to="/admin/dashboard" class="admin-link">
              <el-icon><Setting /></el-icon> 进入后台
            </router-link>
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
import { Setting } from '@element-plus/icons-vue'
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
}
.admin-link {
  text-decoration: none;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}
.admin-link:hover {
  color: #409EFF;
}
</style>