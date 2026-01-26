<template>
  <div v-if="password" class="password-strength-meter">
    <div class="strength-bar">
      <div 
        class="strength-fill"
        :class="strengthClass"
        :style="{ width: strength + '%' }"
      ></div>
    </div>
    <div class="strength-text" :class="strengthClass">
      <i class="bi" :class="strengthIcon"></i>
      {{ strengthMessage }}
    </div>
    <div class="strength-requirements">
      <div class="requirement" :class="{ met: hasMinLength }">
        <i class="bi" :class="hasMinLength ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        At least 12 characters
      </div>
      <div class="requirement" :class="{ met: hasUppercase }">
        <i class="bi" :class="hasUppercase ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One uppercase letter
      </div>
      <div class="requirement" :class="{ met: hasLowercase }">
        <i class="bi" :class="hasLowercase ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One lowercase letter
      </div>
      <div class="requirement" :class="{ met: hasNumber }">
        <i class="bi" :class="hasNumber ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One number
      </div>
      <div class="requirement" :class="{ met: hasSpecial }">
        <i class="bi" :class="hasSpecial ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One special character
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { authAPI } from '../services/api'

const props = defineProps({
  password: {
    type: String,
    required: true
  }
})

const strength = ref(0)
const strengthLevel = ref('weak')
const feedback = ref([])

// Password requirements
const hasMinLength = computed(() => props.password.length >= 12)
const hasUppercase = computed(() => /[A-Z]/.test(props.password))
const hasLowercase = computed(() => /[a-z]/.test(props.password))
const hasNumber = computed(() => /\d/.test(props.password))
const hasSpecial = computed(() => /[!@#$%^&*(),.?":{}|<>]/.test(props.password))

const strengthClass = computed(() => strengthLevel.value)

const strengthIcon = computed(() => {
  if (strengthLevel.value === 'strong') return 'bi-shield-fill-check'
  if (strengthLevel.value === 'medium') return 'bi-shield-fill-exclamation'
  return 'bi-shield-fill-x'
})

const strengthMessage = computed(() => {
  if (strengthLevel.value === 'strong') return 'Strong password'
  if (strengthLevel.value === 'medium') return 'Medium strength'
  return 'Weak password'
})

watch(() => props.password, async (newPassword) => {
  if (!newPassword) {
    strength.value = 0
    strengthLevel.value = 'weak'
    feedback.value = []
    return
  }

  try {
    const response = await authAPI.checkPasswordStrength(newPassword)
    
    // Update based on backend response
    strengthLevel.value = response.data.strength
    strength.value = response.data.score
    feedback.value = response.data.feedback || []
    
  } catch (error) {
    console.error('Error checking password strength:', error)
    // Fallback to client-side calculation
    calculateStrengthClientSide(newPassword)
  }
}, { immediate: true })

// Fallback client-side calculation
const calculateStrengthClientSide = (password) => {
  let score = 0
  
  if (password.length >= 12) score += 25
  else if (password.length >= 8) score += 15
  
  if (/[A-Z]/.test(password)) score += 20
  if (/[a-z]/.test(password)) score += 20
  if (/\d/.test(password)) score += 20
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 15
  
  strength.value = score
  
  if (score >= 80) strengthLevel.value = 'strong'
  else if (score >= 60) strengthLevel.value = 'medium'
  else strengthLevel.value = 'weak'
}
</script>

<style scoped>
.password-strength-meter {
  margin-top: 0.75rem;
}

.strength-bar {
  height: 6px;
  background: var(--gray-200);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.strength-fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.strength-fill.weak {
  background: var(--danger);
}

.strength-fill.medium {
  background: var(--warning);
}

.strength-fill.strong {
  background: var(--success);
}

.strength-text {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.strength-text.weak {
  color: var(--danger);
}

.strength-text.medium {
  color: var(--warning);
}

.strength-text.strong {
  color: var(--success);
}

.strength-requirements {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.requirement {
  font-size: 0.8rem;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  gap: 0.375rem;
  transition: color 0.3s ease;
}

.requirement.met {
  color: var(--success);
}

.requirement i {
  font-size: 0.875rem;
}
</style>