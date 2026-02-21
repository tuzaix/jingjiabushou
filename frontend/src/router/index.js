import { createRouter, createWebHistory } from 'vue-router'
import FrontLayout from '../layouts/FrontLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import Admin from '../views/Admin.vue'
import DataUpdate from '../views/Admin/DataUpdate.vue'

const routes = [
  // Front-end Routes
  {
    path: '/',
    component: FrontLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard
      }
    ]
  },
  // Admin Routes
  {
    path: '/admin',
    component: AdminLayout,
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: Admin,
        meta: { title: '控制台' }
      },
      {
        path: 'import',
        name: 'AdminImport',
        component: DataUpdate,
        meta: { title: '更新数据' }
      },
      {
        path: 'system-config',
        name: 'SystemConfig',
        component: () => import('../views/Admin/SystemConfig.vue'),
        meta: { title: '系统配置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router