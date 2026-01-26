<template>
  <div class="settings-container">
    <div class="settings-card">
      <div class="settings-header">
        <h2><i class="bi bi-shield-lock-fill"></i> Two-Factor Authentication</h2>
        <p>Add an extra layer of security to your account</p>
      </div>

      <div v-if="error" class="alert alert-error">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <span>{{ error }}</span>
      </div>

      <div v-if="success" class="alert alert-success">
        <i class="bi bi-check-circle-fill"></i>
        <span>{{ success }}</span>
      </div>

      <!-- 2FA Status -->
      <div class="status-box" :class="twoFactorEnabled ? 'enabled' : 'disabled'">
        <div class="status-icon">
          <i class="bi" :class="twoFactorEnabled ? 'bi-shield-fill-check' : 'bi-shield-fill-x'"></i>
        </div>
        <div class="status-content">
          <h3>{{ twoFactorEnabled ? 'Enabled' : 'Disabled' }}</h3>
          <p>
            {{ twoFactorEnabled 
              ? 'Your account is protected with 2FA' 
              : 'Enable 2FA to secure your account' 
            }}
          </p>
        </div>
      </div>

      <!-- Enable 2FA Section -->
      <div v-if="!twoFactorEnabled && !showQRCode" class="action-section">
        <h3>Enable Two-Factor Authentication</h3>
        <p>Use an authenticator app like Google Authenticator, Authy, or Microsoft Authenticator.</p>
        
        <button 
          @click="setupTwoFactor" 
          class="btn btn-primary"
          :disabled="loading"
        >
          <i class="bi bi-shield-plus"></i>
          {{ loading ? 'Setting up...' : 'Enable 2FA' }}
        </button>
      </div>

      <!-- QR Code Display -->
      <div v-if="showQRCode" class="qr-section">
        <h3>Step 1: Scan QR Code</h3>
        <p>Open your authenticator app and scan this QR code:</p>
        
        <div class="qr-code-container">
          <img :src="qrCode" alt="2FA QR Code" class="qr-code" />
        </div>

        <div class="secret-key">
          <p><strong>Manual Entry Key:</strong></p>
          <code>{{ secret }}</code>
          <button @click="copySecret" class="btn-copy">
            <i class="bi bi-clipboard"></i>
            Copy
          </button>
        </div>

        <h3>Step 2: Enter Verification Code</h3>
        <p>Enter the 6-digit code from your authenticator app:</p>
        
        <form @submit.prevent="verifyTwoFactor">
          <div class="form-group">
            <input
              v-model="verificationCode"
              type="text"
              class="form-control"
              placeholder="Enter 6-digit code"
              maxlength="6"
              pattern="[0-9]{6}"
              required
              autofocus
            />
          </div>
          
          <div class="button-group">
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="loading || verificationCode.length !== 6"
            >
              <i class="bi bi-check-circle"></i>
              {{ loading ? 'Verifying...' : 'Verify & Enable' }}
            </button>
            <button 
              type="button" 
              @click="cancelSetup" 
              class="btn btn-secondary"
              :disabled="loading"
            >
              <i class="bi bi-x-circle"></i>
              Cancel
            </button>
          </div>
        </form>
      </div>

      <!-- Disable 2FA Section -->
      <div v-if="twoFactorEnabled" class="action-section danger-zone">
        <h3>Disable Two-Factor Authentication</h3>
        <p>Remove 2FA protection from your account. Not recommended.</p>
        
        <button 
          @click="disableTwoFactor" 
          class="btn btn-danger"
          :disabled="loading"
        >
          <i class="bi bi-shield-x"></i>
          {{ loading ? 'Disabling...' : 'Disable 2FA' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authAPI } from '../services/api'

const twoFactorEnabled = ref(false)
const showQRCode = ref(false)
const qrCode = ref('')
const secret = ref('')
const verificationCode = ref('')
const loading = ref(false)
const error = ref(null)
const success = ref(null)

onMounted(async () => {
  await checkTwoFactorStatus()
})

const checkTwoFactorStatus = async () => {
  try {
    const response = await authAPI.getCurrentUser()
    twoFactorEnabled.value = response.data.two_factor_enabled
  } catch (err) {
    console.error('Error checking 2FA status:', err)
  }
}

const setupTwoFactor = async () => {
  error.value = null
  success.value = null
  loading.value = true

  try {
    const response = await authAPI.setup2FA(true)
    qrCode.value = response.data.qr_code
    secret.value = response.data.secret
    showQRCode.value = true
    success.value = 'Scan the QR code with your authenticator app'
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to setup 2FA'
  } finally {
    loading.value = false
  }
}

const verifyTwoFactor = async () => {
  error.value = null
  success.value = null
  loading.value = true

  try {
    await authAPI.verify2FA(verificationCode.value)
    success.value = '2FA enabled successfully!'
    twoFactorEnabled.value = true
    showQRCode.value = false
    verificationCode.value = ''
    qrCode.value = ''
    secret.value = ''
  } catch (err) {
    error.value = err.response?.data?.detail || 'Invalid verification code'
  } finally {
    loading.value = false
  }
}

const disableTwoFactor = async () => {
  if (!confirm('Are you sure you want to disable 2FA? This will make your account less secure.')) {
    return
  }

  error.value = null
  success.value = null
  loading.value = true

  try {
    await authAPI.setup2FA(false)
    success.value = '2FA disabled successfully'
    twoFactorEnabled.value = false
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to disable 2FA'
  } finally {
    loading.value = false
  }
}

const cancelSetup = () => {
  showQRCode.value = false
  verificationCode.value = ''
  qrCode.value = ''
  secret.value = ''
}

const copySecret = () => {
  navigator.clipboard.writeText(secret.value)
  success.value = 'Secret key copied to clipboard!'
  setTimeout(() => {
    success.value = null
  }, 3000)
}
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  padding: 2rem;
  background: var(--gray-50);
}

.settings-card {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.settings-header {
  margin-bottom: 2rem;
  border-bottom: 2px solid var(--gray-200);
  padding-bottom: 1rem;
}

.settings-header h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: var(--gray-900);
}

.settings-header p {
  color: var(--gray-600);
  margin: 0;
}

.status-box {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.status-box.enabled {
  background: #d1fae5;
  border: 2px solid #10b981;
}

.status-box.disabled {
  background: #fee2e2;
  border: 2px solid #ef4444;
}

.status-icon i {
  font-size: 2.5rem;
}

.status-box.enabled .status-icon i {
  color: #10b981;
}

.status-box.disabled .status-icon i {
  color: #ef4444;
}

.status-content h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
}

.status-content p {
  margin: 0;
  color: var(--gray-700);
}

.action-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: var(--gray-50);
  border-radius: 8px;
}

.action-section h3 {
  margin-bottom: 0.5rem;
  color: var(--gray-900);
}

.action-section p {
  margin-bottom: 1rem;
  color: var(--gray-600);
}

.danger-zone {
  background: #fef2f2;
  border: 2px solid #fee2e2;
}

.qr-section {
  margin: 2rem 0;
}

.qr-section h3 {
  margin: 1.5rem 0 0.5rem 0;
  color: var(--gray-900);
}

.qr-section p {
  color: var(--gray-600);
  margin-bottom: 1rem;
}

.qr-code-container {
  display: flex;
  justify-content: center;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  border: 2px solid var(--gray-200);
  margin: 1rem 0;
}

.qr-code {
  max-width: 250px;
  height: auto;
}

.secret-key {
  background: var(--gray-50);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}

.secret-key p {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: var(--gray-700);
}

.secret-key code {
  display: block;
  background: white;
  padding: 0.75rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: var(--primary);
  word-break: break-all;
  margin-bottom: 0.5rem;
}

.btn-copy {
  padding: 0.5rem 1rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.btn-copy:hover {
  background: var(--primary-dark);
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
  transform: translateY(-2px);
}

.btn-secondary {
  background: var(--gray-200);
  color: var(--gray-700);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--gray-300);
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
  transform: translateY(-2px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.alert {
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.alert-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.alert-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
}

.form-group {
  margin-bottom: 1rem;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--gray-300);
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
  text-align: center;
  font-size: 1.5rem;
  letter-spacing: 0.5rem;
  font-weight: 600;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>