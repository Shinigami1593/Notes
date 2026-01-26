<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1><i class="bi bi-shield-lock-fill"></i> Secure Notes</h1>
        <p>Sign in to your account</p>
      </div>

      <div v-if="error" class="alert alert-error">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <span>{{ getErrorMessage(error) }}</span>
      </div>

      <!-- Account Locked Message -->
      <div v-if="accountLocked" class="alert alert-warning">
        <i class="bi bi-lock-fill"></i>
        <span>Your account has been locked due to multiple failed login attempts. Please try again later.</span>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">
            <i class="bi bi-person-fill"></i> Username
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="form-control"
            :class="{ error: errors.username }"
            placeholder="Enter your username"
            required
            autocomplete="username"
            :disabled="show2FAInput"
          />
          <span v-if="errors.username" class="error-text">
            {{ errors.username }}
          </span>
        </div>

        <div class="form-group">
          <label for="password">
            <i class="bi bi-key-fill"></i> Password
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="form-control"
            :class="{ error: errors.password }"
            placeholder="Enter your password"
            required
            autocomplete="current-password"
            :disabled="show2FAInput"
          />
          <span v-if="errors.password" class="error-text">
            {{ errors.password }}
          </span>
        </div>

        <!-- 2FA Token Input -->
        <div v-if="show2FAInput" class="form-group">
          <label for="two-factor-token">
            <i class="bi bi-shield-check"></i> Two-Factor Authentication Code
          </label>
          <input
            id="two-factor-token"
            v-model="twoFactorToken"
            type="text"
            class="form-control"
            :class="{ error: errors.twoFactorToken }"
            placeholder="Enter 6-digit code"
            maxlength="6"
            pattern="[0-9]{6}"
            required
          />
          <span class="form-help">
            <i class="bi bi-info-circle"></i>
            Enter the 6-digit code from your authenticator app
          </span>
          <span v-if="errors.twoFactorToken" class="error-text">
            {{ errors.twoFactorToken }}
          </span>
        </div>

        <button 
          type="submit" 
          class="btn btn-primary btn-block"
          :disabled="loading"
        >
          <i class="bi" :class="loading ? 'bi-hourglass-split' : 'bi-box-arrow-in-right'"></i>
          {{ loading ? 'Signing in...' : (show2FAInput ? 'Verify & Sign In' : 'Sign In') }}
        </button>
      </form>

      <div class="auth-footer">
        Don't have an account? 
        <router-link to="/register" class="link">Create one</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authAPI } from '../services/api'
import { useRouter } from 'vue-router'

const router = useRouter()

const username = ref('')
const password = ref('')
const twoFactorToken = ref('')
const show2FAInput = ref(false)
const accountLocked = ref(false)
const errors = ref({})
const loading = ref(false)
const error = ref(null)

const handleLogin = async () => {
  errors.value = {}
  error.value = null
  accountLocked.value = false
  
  if (!username.value.trim()) {
    errors.value.username = 'Username is required'
    return
  }
  
  if (!password.value) {
    errors.value.password = 'Password is required'
    return
  }
  
  if (show2FAInput.value && !twoFactorToken.value) {
    errors.value.twoFactorToken = '2FA code is required'
    return
  }
  
  try {
    loading.value = true
    
    // Send login request with 2FA token if required
    const response = await authAPI.login(
      username.value,
      password.value,
      show2FAInput.value ? twoFactorToken.value : ''
    )
    
    if (response.data.two_factor_required) {
      // 2FA is required, show the 2FA input field
      show2FAInput.value = true
      error.value = null
    } else if (response.data.password_expired) {
      alert('Your password has expired. Please change it.')
    } else {
      // Login successful, store tokens
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      
      console.log('Login successful, token stored')
      
      // Redirect to dashboard
      router.push('/dashboard')
    }
  } catch (err) {
    console.error('Login failed:', err)
    
    if (err.response?.status === 403) {
      accountLocked.value = true
    }
    
    error.value = err.response?.data?.detail || 'Login failed'
    
    // Reset 2FA input if verification failed
    if (show2FAInput.value) {
      twoFactorToken.value = ''
    } else {
      show2FAInput.value = false
      twoFactorToken.value = ''
    }
  } finally {
    loading.value = false
  }
}

const getErrorMessage = (error) => {
  if (typeof error === 'string') {
    return error
  }
  if (error.detail) {
    return error.detail
  }
  return 'Login failed. Please check your credentials.'
}
</script>