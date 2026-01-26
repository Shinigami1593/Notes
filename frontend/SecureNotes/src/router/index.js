import { createRouter, createWebHistory } from 'vue-router'
import { authAPI } from '../services/api'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import CreateNote from '../views/CreateNote.vue'
import EditNote from '../views/EditNote.vue'
import Profile from '../views/Profile.vue'
import Transactions from '../views/Transactions.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/notes/create',
    name: 'CreateNote',
    component: CreateNote,
    meta: { requiresAuth: true }
  },
  {
    path: '/notes/:id/edit',
    name: 'EditNote',
    component: EditNote,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/billing',
    name: 'Transactions',
    component: Transactions,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings/2fa',
    name: 'TwoFactorSetup',
    component: () => import('../views/TwoFactorSetup.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Enhanced: Navigation guard with security checks
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)

  // Path traversal security check
  if (to.path.includes('..') || to.path.includes('//')) {
    next('/login')
    return
  }

  // If route doesn't require auth or guest, allow navigation
  if (!requiresAuth && !requiresGuest) {
    next()
    return
  }

  let isAuthenticated = false
  let currentUser = null
  
  // Check authentication status with token validation
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      isAuthenticated = false
    } else {
      // Verify token is still valid
      currentUser = await authAPI.getCurrentUser()
      isAuthenticated = true
    }
  } catch (error) {
    isAuthenticated = false
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // Route requires authentication
  if (requiresAuth && !isAuthenticated) {
    // Redirect to login with return URL
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }
  
  // Route requires guest (login/register pages)
  if (requiresGuest && isAuthenticated) {
    next('/dashboard')
    return
  }
  
  // Allow navigation
  next()
})

export default router