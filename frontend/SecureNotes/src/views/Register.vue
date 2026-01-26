<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1><i class="bi bi-shield-lock-fill"></i> Secure Notes</h1>
        <p>Create your account</p>
      </div>

      <div v-if="error" class="alert alert-error">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <div>
          <div v-if="typeof error === 'string'">{{ error }}</div>
          <div v-else>
            <div v-for="(messages, field) in error" :key="field">
              <strong>{{ field }}:</strong> 
              {{ Array.isArray(messages) ? messages.join(', ') : messages }}
            </div>
          </div>
        </div>
      </div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="username">
            <i class="bi bi-person-fill"></i> Username
          </label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            class="form-control"
            :class="{ error: errors.username }"
            placeholder="Choose a username (min 3 characters)"
            required
            autocomplete="username"
          />
          <span v-if="errors.username" class="error-text">
            {{ errors.username }}
          </span>
        </div>

        <div class="form-group">
          <label for="email">
            <i class="bi bi-envelope-fill"></i> Email
          </label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            class="form-control"
            :class="{ error: errors.email }"
            placeholder="Enter your email"
            required
            autocomplete="email"
          />
          <span v-if="errors.email" class="error-text">
            {{ errors.email }}
          </span>
        </div>

        <div class="form-group">
          <label for="password">
            <i class="bi bi-key-fill"></i> Password
          </label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            class="form-control"
            :class="{ error: errors.password }"
            placeholder="Create a strong password"
            required
            autocomplete="new-password"
          />
          <span v-if="errors.password" class="error-text">
            {{ errors.password }}
          </span>
          
          <!-- Password Strength Meter -->
          <PasswordStrengthMeter :password="formData.password" />
        </div>

        <div class="form-group">
          <label for="password2">
            <i class="bi bi-key-fill"></i> Confirm Password
          </label>
          <input
            id="password2"
            v-model="formData.password2"
            type="password"
            class="form-control"
            :class="{ error: errors.password2 }"
            placeholder="Confirm your password"
            required
            autocomplete="new-password"
          />
          <span v-if="errors.password2" class="error-text">
            {{ errors.password2 }}
          </span>
        </div>

        <button 
          type="submit" 
          class="btn btn-primary btn-block"
          :disabled="loading"
        >
          <i class="bi" :class="loading ? 'bi-hourglass-split' : 'bi-person-plus-fill'"></i>
          {{ loading ? 'Creating Account...' : 'Create Account' }}
        </button>
      </form>

      <div class="auth-footer">
        Already have an account? 
        <router-link to="/login" class="link">Sign in</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth'
import PasswordStrengthMeter from '../components/PasswordStrengthMeter.vue'

const { register, loading, error } = useAuth()

const formData = ref({
  username: '',
  email: '',
  password: '',
  password2: ''
})

const errors = ref({})

const handleRegister = async () => {
  errors.value = {}
  
  // Client-side validation
  if (!formData.value.username.trim()) {
    errors.value.username = 'Username is required'
    return
  }
  
  if (formData.value.username.length < 3) {
    errors.value.username = 'Username must be at least 3 characters'
    return
  }
  
  if (!formData.value.email.trim()) {
    errors.value.email = 'Email is required'
    return
  }
  
  if (!formData.value.password) {
    errors.value.password = 'Password is required'
    return
  }
  
  if (formData.value.password.length < 12) {
    errors.value.password = 'Password must be at least 12 characters'
    return
  }
  
  if (formData.value.password !== formData.value.password2) {
    errors.value.password2 = 'Passwords do not match'
    return
  }
  
  try {
    await register(
      formData.value.username,
      formData.value.email,
      formData.value.password,
      formData.value.password2
    )
    // Navigation happens in useAuth composable
    console.log('Registration completed, redirecting...')
  } catch (err) {
    console.error('Registration failed:', err)
    // Error is already set in useAuth composable
  }
}
</script>