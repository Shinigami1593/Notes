<template>
  <nav class="app-navbar">
    <div class="navbar-container">
      <!-- Logo & Brand -->
      <router-link to="/dashboard" class="navbar-brand">
        <i class="bi bi-shield-lock-fill"></i>
        Secure Notes
      </router-link>

      <!-- Navigation Links -->
      <div class="navbar-menu">
        <router-link 
          to="/dashboard" 
          class="nav-link"
          :class="{ active: isActive('/dashboard') }"
          aria-label="Dashboard"
        >
          <i class="bi bi-house-fill"></i>
          <span>Dashboard</span>
        </router-link>

        <router-link 
          to="/profile" 
          class="nav-link"
          :class="{ active: isActive('/profile') }"
          aria-label="My Profile"
        >
          <i class="bi bi-person-fill"></i>
          <span>Profile</span>
        </router-link>

        <router-link 
          to="/billing" 
          class="nav-link"
          :class="{ active: isActive('/billing') }"
          aria-label="Billing & Subscription"
        >
          <i class="bi bi-credit-card-fill"></i>
          <span>Billing</span>
        </router-link>

        <router-link 
          to="/settings/2fa" 
          class="nav-link"
          :class="{ active: isActive('/settings') }"
          aria-label="Settings"
        >
          <i class="bi bi-gear-fill"></i>
          <span>Settings</span>
        </router-link>
      </div>

      <!-- User Menu -->
      <div class="navbar-user">
        <div class="user-info" v-if="currentUser">
          <img 
            v-if="currentUser.avatar_url" 
            :src="currentUser.avatar_url" 
            :alt="currentUser.username"
            class="user-avatar"
          />
          <div v-else class="user-avatar-placeholder">
            {{ currentUser.username.charAt(0).toUpperCase() }}
          </div>
          <div class="user-details">
            <p class="username">{{ currentUser.username }}</p>
            <p v-if="currentPlan" class="plan-badge" :class="`plan-${currentPlan}`">
              {{ planLabel }}
            </p>
          </div>
        </div>

        <!-- Dropdown Menu -->
        <div class="dropdown">
          <button 
            @click="showDropdown = !showDropdown"
            class="dropdown-toggle"
            aria-haspopup="true"
            :aria-expanded="showDropdown"
            aria-label="User menu"
          >
            <i class="bi bi-chevron-down"></i>
          </button>

          <div v-if="showDropdown" class="dropdown-menu">
            <router-link 
              to="/profile" 
              class="dropdown-item"
              @click="showDropdown = false"
            >
              <i class="bi bi-person-circle"></i>
              My Profile
            </router-link>
            <router-link 
              to="/billing" 
              class="dropdown-item"
              @click="showDropdown = false"
            >
              <i class="bi bi-credit-card"></i>
              Billing & Subscription
            </router-link>
            <router-link 
              to="/settings/2fa" 
              class="dropdown-item"
              @click="showDropdown = false"
            >
              <i class="bi bi-shield-check"></i>
              Security Settings
            </router-link>
            
            <div class="dropdown-divider"></div>

            <button 
              @click="handleLogout"
              class="dropdown-item logout"
            >
              <i class="bi bi-box-arrow-right"></i>
              Logout
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile Menu Toggle -->
      <button 
        @click="showMobileMenu = !showMobileMenu"
        class="mobile-menu-toggle"
        aria-label="Toggle menu"
        v-if="isMobile"
      >
        <i class="bi" :class="showMobileMenu ? 'bi-x-lg' : 'bi-list'"></i>
      </button>
    </div>

    <!-- Mobile Menu -->
    <div v-if="showMobileMenu" class="mobile-menu">
      <router-link 
        to="/dashboard" 
        class="mobile-nav-link"
        @click="showMobileMenu = false"
      >
        <i class="bi bi-house-fill"></i>
        Dashboard
      </router-link>

      <router-link 
        to="/profile" 
        class="mobile-nav-link"
        @click="showMobileMenu = false"
      >
        <i class="bi bi-person-fill"></i>
        Profile
      </router-link>

      <router-link 
        to="/billing" 
        class="mobile-nav-link"
        @click="showMobileMenu = false"
      >
        <i class="bi bi-credit-card-fill"></i>
        Billing
      </router-link>

      <router-link 
        to="/settings/2fa" 
        class="mobile-nav-link"
        @click="showMobileMenu = false"
      >
        <i class="bi bi-gear-fill"></i>
        Settings
      </router-link>

      <button 
        @click="handleLogout"
        class="mobile-nav-link logout"
      >
        <i class="bi bi-box-arrow-right"></i>
        Logout
      </button>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authAPI } from '../services/api'

const router = useRouter()
const route = useRoute()
const showDropdown = ref(false)
const showMobileMenu = ref(false)
const currentUser = ref(null)
const currentPlan = ref('free')
const isMobile = ref(false)

const planLabel = computed(() => {
  const labels = {
    'free': 'Free Plan',
    'pro': 'Pro Plan',
    'enterprise': 'Enterprise'
  }
  return labels[currentPlan.value] || 'Free Plan'
})

onMounted(async () => {
  await loadCurrentUser()
  checkMobileScreen()
  window.addEventListener('resize', checkMobileScreen)
})

const loadCurrentUser = async () => {
  try {
    const response = await authAPI.getCurrentUser()
    currentUser.value = response.data
  } catch (error) {
    console.error('Error loading user:', error)
  }
}

const checkMobileScreen = () => {
  isMobile.value = window.innerWidth <= 768
}

const isActive = (path) => {
  return route.path.startsWith(path)
}

const handleLogout = async () => {
  try {
    await authAPI.logout()
    showDropdown.value = false
    showMobileMenu.value = false
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
    router.push('/login')
  }
}
</script>

<style scoped>
.app-navbar {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.navbar-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: bold;
  text-decoration: none;
  color: white;
  transition: transform 0.3s ease;
  flex-shrink: 0;
}

.navbar-brand:hover {
  transform: scale(1.05);
}

.navbar-brand i {
  font-size: 1.75rem;
}

.navbar-menu {
  display: flex;
  gap: 2rem;
  flex: 1;
  align-items: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  font-weight: 500;
  white-space: nowrap;
}

.nav-link:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-link.active {
  color: white;
  background: rgba(255, 255, 255, 0.2);
  border-bottom: 2px solid white;
}

.nav-link i {
  font-size: 1.1rem;
}

.navbar-user {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar,
.user-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.1rem;
  background: rgba(255, 255, 255, 0.2);
}

.user-avatar {
  object-fit: cover;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.username {
  margin: 0;
  font-weight: 600;
  font-size: 0.95rem;
}

.plan-badge {
  margin: 0;
  font-size: 0.75rem;
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.plan-free {
  color: #e0e0e0;
}

.plan-pro {
  color: #ffd700;
}

.plan-enterprise {
  color: #ff6b6b;
}

.dropdown {
  position: relative;
}

.dropdown-toggle {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  font-size: 1.1rem;
}

.dropdown-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  min-width: 220px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: #333;
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: all 0.3s ease;
  font-size: 0.95rem;
}

.dropdown-item:hover {
  background: #f5f5f5;
  color: #667eea;
}

.dropdown-item i {
  font-size: 1.1rem;
  min-width: 20px;
}

.dropdown-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 0.5rem 0;
}

.dropdown-item.logout {
  color: #ef4444;
}

.dropdown-item.logout:hover {
  background: #fee2e2;
  color: #dc2626;
}

.mobile-menu-toggle {
  display: none;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.3rem;
}

.mobile-menu {
  display: none;
  background: rgba(0, 0, 0, 0.1);
  padding: 1rem;
  flex-direction: column;
  gap: 0.5rem;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: white;
  text-decoration: none;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.mobile-nav-link:hover {
  background: rgba(255, 255, 255, 0.2);
}

.mobile-nav-link.logout {
  color: #ffc0c0;
}

@media (max-width: 768px) {
  .navbar-container {
    padding: 1rem;
    gap: 1rem;
  }

  .navbar-brand {
    font-size: 1.3rem;
  }

  .navbar-brand span {
    display: none;
  }

  .navbar-menu {
    display: none;
  }

  .mobile-menu-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mobile-menu {
    display: flex;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    flex-direction: column;
    width: 100%;
  }

  .user-details {
    display: none;
  }

  .user-info {
    gap: 0;
  }
}
</style>
