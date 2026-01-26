<template>
  <div class="settings-container">
    <!-- Navigation -->
    <AppNavbar />

    <!-- Main Content -->
    <div class="container">
      <!-- Page Header -->
      <div class="page-header">
        <h1><i class="bi bi-gear-fill"></i> Settings & Security</h1>
        <router-link to="/dashboard" class="btn btn-secondary">
          <i class="bi bi-arrow-left"></i>
          Back to Dashboard
        </router-link>
      </div>

      <!-- Alert Messages -->
      <div v-if="successMessage" class="alert alert-success" role="alert">
        <i class="bi bi-check-circle-fill"></i>
        <span>{{ successMessage }}</span>
      </div>
      <div v-if="errorMessage" class="alert alert-error" role="alert">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <span>{{ errorMessage }}</span>
      </div>

      <!-- Settings Grid -->
      <div class="settings-grid">
        <!-- Sidebar Navigation -->
        <aside class="settings-sidebar" role="navigation" aria-label="Settings sections">
          <nav class="settings-nav">
            <button
              v-for="section in sections"
              :key="section.id"
              @click="activeTab = section.id"
              :class="['nav-item', { active: activeTab === section.id }]"
              :aria-current="activeTab === section.id ? 'page' : 'false'"
              :aria-label="section.label"
            >
              <i :class="section.icon"></i>
              {{ section.label }}
            </button>
          </nav>
        </aside>

        <!-- Settings Content -->
        <main class="settings-main">
          <!-- Password Section -->
          <section v-if="activeTab === 'password'" class="settings-section" aria-labelledby="password-heading">
            <h2 id="password-heading"><i class="bi bi-lock-fill"></i> Change Password</h2>
            <p class="section-description">Update your account password regularly to keep your account secure</p>
            
            <form @submit.prevent="changePassword" class="form">
              <div class="form-group">
                <label for="oldPassword">
                  <i class="bi bi-key"></i>
                  Current Password
                </label>
                <input
                  id="oldPassword"
                  v-model="passwordForm.oldPassword"
                  type="password"
                  class="form-control"
                  required
                  aria-describedby="oldPassword-help"
                />
                <small id="oldPassword-help">For security, we need your current password</small>
              </div>

              <div class="form-group">
                <label for="newPassword">
                  <i class="bi bi-shield-check"></i>
                  New Password
                </label>
                <input
                  id="newPassword"
                  v-model="passwordForm.newPassword"
                  type="password"
                  class="form-control"
                  required
                  @input="checkPasswordStrength"
                  aria-describedby="newPassword-help strength-meter"
                />
                <small id="newPassword-help">At least 8 characters with mix of uppercase, lowercase, numbers and symbols</small>
                
                <!-- Password Strength Meter -->
                <div id="strength-meter" class="strength-indicator">
                  <div class="strength-bar">
                    <div 
                      :class="['strength-fill', `strength-${passwordStrength.level}`]"
                      :style="{ width: passwordStrength.percentage + '%' }"
                    ></div>
                  </div>
                  <p :class="['strength-text', `strength-${passwordStrength.level}`]">
                    {{ passwordStrength.text }}
                  </p>
                </div>
              </div>

              <div class="form-group">
                <label for="confirmPassword">
                  <i class="bi bi-check-circle"></i>
                  Confirm New Password
                </label>
                <input
                  id="confirmPassword"
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  class="form-control"
                  required
                  aria-describedby="confirmPassword-help"
                />
                <small id="confirmPassword-help">Must match the new password above</small>
              </div>

              <div class="form-actions">
                <button type="submit" class="btn btn-primary" :disabled="loading">
                  <i :class="loading ? 'bi-hourglass-split' : 'bi-check-circle'"></i>
                  {{ loading ? 'Updating...' : 'Update Password' }}
                </button>
              </div>
            </form>
          </section>

          <!-- 2FA Section -->
          <section v-if="activeTab === 'twofa'" class="settings-section" aria-labelledby="twofa-heading">
            <h2 id="twofa-heading"><i class="bi bi-shield-check"></i> Two-Factor Authentication</h2>
            <p class="section-description">Add an extra layer of security with 2FA using an authenticator app</p>
            
            <!-- 2FA Enabled State -->
            <div v-if="twoFactorEnabled && !showQRCode" class="security-status">
              <div class="status-badge status-success">
                <i class="bi bi-shield-check"></i>
                <span>2FA is enabled</span>
              </div>
              <p class="mt-2">Your account is protected with two-factor authentication. Make sure you have your backup codes saved.</p>
              <button 
                @click="showDisable2FAConfirm = true"
                class="btn btn-danger mt-2"
              >
                <i class="bi bi-shield-x"></i>
                Disable 2FA
              </button>

              <!-- Disable Confirmation -->
              <div v-if="showDisable2FAConfirm" class="confirmation-dialog">
                <h4>Are you sure you want to disable 2FA?</h4>
                <p>Your account will be less secure. This action cannot be undone immediately.</p>
                <div class="dialog-actions">
                  <button @click="disable2FA" class="btn btn-danger">Disable 2FA</button>
                  <button @click="showDisable2FAConfirm = false" class="btn btn-secondary">Cancel</button>
                </div>
              </div>
            </div>

            <!-- 2FA Disabled State -->
            <div v-else-if="!twoFactorEnabled && !showQRCode" class="security-status">
              <div class="status-badge status-warning">
                <i class="bi bi-shield-exclamation"></i>
                <span>2FA is not enabled</span>
              </div>
              <p class="mt-2">Enable two-factor authentication to protect your account from unauthorized access.</p>
              <button 
                @click="enable2FA" 
                class="btn btn-primary mt-2"
                :disabled="loading"
              >
                <i class="bi bi-shield-plus"></i>
                {{ loading ? 'Loading...' : 'Enable 2FA' }}
              </button>
            </div>

            <!-- QR Code Display -->
            <div v-if="showQRCode" class="qr-code-section">
              <h3><i class="bi bi-qr-code"></i> Scan to Enable 2FA</h3>
              <p>Use Google Authenticator, Authy, or Microsoft Authenticator to scan this QR code:</p>
              
              <div class="qr-code-container">
                <img v-if="qrCode" :src="qrCode" alt="QR Code for 2FA setup" class="qr-code-image" />
              </div>

              <div class="secret-key-section">
                <p><strong>Can't scan?</strong> Enter this code manually:</p>
                <div class="secret-key-display">
                  <code>{{ secretKey }}</code>
                  <button 
                    @click="copySecret"
                    class="btn btn-secondary btn-sm"
                    title="Copy secret key"
                  >
                    <i class="bi bi-clipboard"></i>
                    Copy
                  </button>
                </div>
              </div>

              <form @submit.prevent="confirm2FA" class="mt-3">
                <div class="form-group">
                  <label for="verificationCode">
                    <i class="bi bi-123"></i>
                    Verification Code
                  </label>
                  <input
                    id="verificationCode"
                    v-model="verificationCode"
                    type="text"
                    class="form-control"
                    placeholder="000000"
                    maxlength="6"
                    required
                    aria-describedby="code-help"
                  />
                  <small id="code-help">Enter the 6-digit code from your authenticator app</small>
                </div>

                <div class="form-actions">
                  <button type="submit" class="btn btn-primary" :disabled="loading">
                    <i class="bi bi-check-circle"></i>
                    {{ loading ? 'Verifying...' : 'Verify & Enable' }}
                  </button>
                  <button 
                    type="button"
                    @click="cancelEnable2FA"
                    class="btn btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </section>

          <!-- Account Security Section -->
          <section v-if="activeTab === 'security'" class="settings-section" aria-labelledby="security-heading">
            <h2 id="security-heading"><i class="bi bi-shield-lock"></i> Account Security</h2>
            <p class="section-description">Review and manage your account security settings</p>
            
            <div class="security-checklist">
              <div class="checklist-item">
                <div class="check-icon" :class="{ checked: accountSecurityStatus.strongPassword }">
                  <i class="bi bi-check"></i>
                </div>
                <div class="check-content">
                  <h4>Strong Password</h4>
                  <p>Use a unique, strong password for your account</p>
                </div>
                <button class="btn btn-sm btn-secondary" @click="activeTab = 'password'">Review</button>
              </div>

              <div class="checklist-item">
                <div class="check-icon" :class="{ checked: accountSecurityStatus.twoFactor }">
                  <i class="bi bi-check"></i>
                </div>
                <div class="check-content">
                  <h4>Two-Factor Authentication</h4>
                  <p>Enable 2FA to add an extra security layer</p>
                </div>
                <span v-if="twoFactorEnabled" class="status-badge status-success">Enabled</span>
                <span v-else class="status-badge status-warning">Not Enabled</span>
              </div>

              <div class="checklist-item">
                <div class="check-icon" :class="{ checked: accountSecurityStatus.recentActivity }">
                  <i class="bi bi-check"></i>
                </div>
                <div class="check-content">
                  <h4>Recent Activity</h4>
                  <p>Monitor your account activity and active sessions</p>
                </div>
                <router-link to="/profile" class="btn btn-sm btn-secondary">View Sessions</router-link>
              </div>

              <div class="checklist-item">
                <div class="check-icon" :class="{ checked: accountSecurityStatus.notifications }">
                  <i class="bi bi-check"></i>
                </div>
                <div class="check-content">
                  <h4>Security Notifications</h4>
                  <p>Get alerts for suspicious activity</p>
                </div>
                <router-link to="/profile" class="btn btn-sm btn-secondary">Configure</router-link>
              </div>
            </div>

            <!-- Account Activity Summary -->
            <div class="activity-summary" style="margin-top: 2rem;">
              <h3><i class="bi bi-activity"></i> Account Activity</h3>
              <div class="activity-stats">
                <div class="stat-card">
                  <div class="stat-value">{{ lastLoginDate }}</div>
                  <div class="stat-label">Last Login</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ failedAttempts }}</div>
                  <div class="stat-label">Failed Attempts</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ accountCreatedDate }}</div>
                  <div class="stat-label">Account Created</div>
                </div>
              </div>
            </div>
          </section>

          <!-- Profile Links Section -->
          <section v-if="activeTab === 'profile'" class="settings-section" aria-labelledby="profile-heading">
            <h2 id="profile-heading"><i class="bi bi-person"></i> Profile & Account</h2>
            <p class="section-description">Manage your profile information and account settings</p>
            
            <div class="quick-links">
              <router-link to="/profile" class="link-card">
                <i class="bi bi-person-circle"></i>
                <h3>Edit Profile</h3>
                <p>Update your personal information, bio, and preferences</p>
              </router-link>

              <router-link to="/billing" class="link-card">
                <i class="bi bi-credit-card"></i>
                <h3>Billing & Subscription</h3>
                <p>Manage your subscription plan and payment methods</p>
              </router-link>

              <router-link to="/profile" class="link-card">
                <i class="bi bi-cloud-check"></i>
                <h3>Active Sessions</h3>
                <p>View and manage your active login sessions</p>
              </router-link>

              <a href="#" class="link-card" @click.prevent="showPrivacyPolicy = true">
                <i class="bi bi-shield-check"></i>
                <h3>Privacy & Security</h3>
                <p>Review our privacy policy and security measures</p>
              </a>
            </div>
          </section>

          <!-- Data & Privacy Section -->
          <section v-if="activeTab === 'privacy'" class="settings-section" aria-labelledby="privacy-heading">
            <h2 id="privacy-heading"><i class="bi bi-lock"></i> Data & Privacy</h2>
            <p class="section-description">Control how your data is used and managed</p>
            
            <div class="privacy-options">
              <div class="privacy-card">
                <h3><i class="bi bi-download"></i> Download Your Data</h3>
                <p>Export all your notes and account data in JSON format</p>
                <button class="btn btn-secondary">
                  <i class="bi bi-download"></i>
                  Download Data
                </button>
              </div>

              <div class="privacy-card">
                <h3><i class="bi bi-trash"></i> Delete Account</h3>
                <p>Permanently delete your account and all associated data</p>
                <button class="btn btn-danger">
                  <i class="bi bi-trash"></i>
                  Delete Account
                </button>
              </div>

              <div class="privacy-card">
                <h3><i class="bi bi-clock-history"></i> Data Retention</h3>
                <p>We keep your data encrypted and secure on our servers</p>
                <p style="color: #999; font-size: 0.9rem;">Learn more in our privacy policy</p>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'
import AppNavbar from '../components/AppNavbar.vue'

const router = useRouter()
const activeTab = ref('password')
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// State
const currentUser = ref(null)
const twoFactorEnabled = ref(false)
const showQRCode = ref(false)
const showDisable2FAConfirm = ref(false)
const showPrivacyPolicy = ref(false)
const qrCode = ref('')
const secretKey = ref('')
const verificationCode = ref('')

const sections = [
  { id: 'password', label: 'Password', icon: 'bi bi-lock-fill' },
  { id: 'twofa', label: '2FA', icon: 'bi bi-shield-check' },
  { id: 'security', label: 'Security', icon: 'bi bi-shield-lock' },
  { id: 'profile', label: 'Profile', icon: 'bi bi-person-fill' },
  { id: 'privacy', label: 'Privacy', icon: 'bi bi-lock' },
]

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordStrength = ref({
  level: 'weak',
  percentage: 0,
  text: 'Weak password'
})

const accountSecurityStatus = ref({
  strongPassword: false,
  twoFactor: false,
  recentActivity: true,
  notifications: true
})

const lastLoginDate = ref('Today at 2:30 PM')
const failedAttempts = ref('0')
const accountCreatedDate = ref('Jan 15, 2024')

onMounted(async () => {
  await loadCurrentUser()
})

const loadCurrentUser = async () => {
  try {
    const response = await authAPI.getCurrentUser()
    currentUser.value = response.data
    // Check 2FA status
    twoFactorEnabled.value = response.data.two_factor_enabled || false
    accountSecurityStatus.value.twoFactor = twoFactorEnabled.value
  } catch (error) {
    console.error('Error loading user:', error)
    errorMessage.value = 'Failed to load user data'
  }
}

const checkPasswordStrength = () => {
  const password = passwordForm.value.newPassword
  let strength = 0
  let level = 'weak'
  let text = 'Weak password'

  if (password.length >= 8) strength += 20
  if (password.length >= 12) strength += 10
  if (/[a-z]/.test(password)) strength += 15
  if (/[A-Z]/.test(password)) strength += 15
  if (/[0-9]/.test(password)) strength += 20
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 20

  if (strength < 30) {
    level = 'weak'
    text = 'Weak password'
  } else if (strength < 60) {
    level = 'fair'
    text = 'Fair password'
  } else if (strength < 80) {
    level = 'good'
    text = 'Good password'
  } else {
    level = 'strong'
    text = 'Strong password'
  }

  passwordStrength.value = {
    level,
    percentage: Math.min(strength, 100),
    text
  }
}

const changePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    errorMessage.value = 'Passwords do not match'
    return
  }

  if (passwordForm.value.newPassword.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters'
    return
  }

  loading.value = true
  try {
    await authAPI.changePassword(
      passwordForm.value.oldPassword,
      passwordForm.value.newPassword
    )
    successMessage.value = 'Password changed successfully'
    passwordForm.value = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
    passwordStrength.value = { level: 'weak', percentage: 0, text: 'Weak password' }
    setTimeout(() => successMessage.value = '', 3000)
  } catch (error) {
    console.error('Error changing password:', error)
    errorMessage.value = error.response?.data?.detail || 'Failed to change password'
  } finally {
    loading.value = false
  }
}

const enable2FA = async () => {
  loading.value = true
  try {
    const response = await authAPI.setup2FA(true)
    qrCode.value = response.data.qr_code
    secretKey.value = response.data.secret_key
    showQRCode.value = true
    verificationCode.value = ''
  } catch (error) {
    console.error('Error enabling 2FA:', error)
    errorMessage.value = 'Failed to enable 2FA'
  } finally {
    loading.value = false
  }
}

const confirm2FA = async () => {
  if (verificationCode.value.length !== 6) {
    errorMessage.value = 'Please enter a 6-digit code'
    return
  }

  loading.value = true
  try {
    await authAPI.verify2FA(verificationCode.value, currentUser.value.username)
    successMessage.value = '2FA enabled successfully'
    twoFactorEnabled.value = true
    accountSecurityStatus.value.twoFactor = true
    showQRCode.value = false
    qrCode.value = ''
    secretKey.value = ''
    setTimeout(() => successMessage.value = '', 3000)
  } catch (error) {
    console.error('Error confirming 2FA:', error)
    errorMessage.value = 'Invalid verification code'
  } finally {
    loading.value = false
  }
}

const disable2FA = async () => {
  loading.value = true
  try {
    await authAPI.setup2FA(false)
    successMessage.value = '2FA disabled'
    twoFactorEnabled.value = false
    accountSecurityStatus.value.twoFactor = false
    showDisable2FAConfirm.value = false
    setTimeout(() => successMessage.value = '', 3000)
  } catch (error) {
    console.error('Error disabling 2FA:', error)
    errorMessage.value = 'Failed to disable 2FA'
  } finally {
    loading.value = false
  }
}

const cancelEnable2FA = () => {
  showQRCode.value = false
  qrCode.value = ''
  secretKey.value = ''
  verificationCode.value = ''
}

const copySecret = async () => {
  try {
    await navigator.clipboard.writeText(secretKey.value)
    successMessage.value = 'Secret key copied to clipboard'
    setTimeout(() => successMessage.value = '', 2000)
  } catch (error) {
    errorMessage.value = 'Failed to copy'
  }
}

const handleLogout = async () => {
  try {
    await authAPI.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
    router.push('/login')
  }
}
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.navbar {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-brand {
  color: #667eea;
  font-size: 1.5rem;
  font-weight: bold;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.navbar-user {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
}

.container {
  max-width: 1400px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.page-header h1 {
  margin: 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.alert {
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.alert-success {
  background: #d1fae5;
  border: 1px solid #10b981;
  color: #065f46;
}

.alert-error {
  background: #fee2e2;
  border: 1px solid #ef4444;
  color: #991b1b;
}

.settings-grid {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 2rem;
}

.settings-sidebar {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  height: fit-content;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-item {
  background: none;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #666;
  transition: all 0.3s ease;
  text-align: left;
  font-weight: 500;
}

.nav-item:hover {
  background: #f0f0f0;
  color: #667eea;
}

.nav-item.active {
  background: #f0f4ff;
  color: #667eea;
  border-left: 3px solid #667eea;
  padding-left: calc(1rem - 3px);
}

.settings-main {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.settings-section {
  display: block;
  margin-bottom: 2rem;
}

.settings-section h2 {
  margin: 0 0 0.5rem 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
}

.section-description {
  margin: 0.5rem 0 1.5rem 0;
  color: #666;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-control {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  transition: all 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-control small {
  color: #999;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.strength-indicator {
  margin-top: 1rem;
}

.strength-bar {
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.strength-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 3px;
}

.strength-fill.strength-weak {
  background: #ef4444;
}

.strength-fill.strength-fair {
  background: #f59e0b;
}

.strength-fill.strength-good {
  background: #3b82f6;
}

.strength-fill.strength-strong {
  background: #10b981;
}

.strength-text {
  font-size: 0.85rem;
  margin: 0;
}

.strength-text.strength-weak {
  color: #ef4444;
}

.strength-text.strength-fair {
  color: #f59e0b;
}

.strength-text.strength-good {
  color: #3b82f6;
}

.strength-text.strength-strong {
  color: #10b981;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 2px solid #e5e7eb;
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
  text-decoration: none;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e5e7eb;
  color: #666;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.security-status {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #667eea;
  margin-bottom: 1.5rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  margin-bottom: 1rem;
}

.status-badge.status-success {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.status-warning {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.status-error {
  background: #fee2e2;
  color: #991b1b;
}

.qr-code-section {
  background: #f9fafb;
  padding: 2rem;
  border-radius: 8px;
  text-align: center;
}

.qr-code-section h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.qr-code-container {
  margin: 1.5rem 0;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  display: inline-block;
}

.qr-code-image {
  max-width: 250px;
  border: 3px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.secret-key-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid #e5e7eb;
}

.secret-key-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  margin: 0.75rem 0;
}

.secret-key-display code {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: bold;
  letter-spacing: 2px;
}

.confirmation-dialog {
  background: #fee2e2;
  border: 2px solid #ef4444;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1rem;
}

.confirmation-dialog h4 {
  margin: 0 0 0.5rem 0;
  color: #991b1b;
}

.confirmation-dialog p {
  margin: 0 0 1rem 0;
  color: #7c2d12;
}

.dialog-actions {
  display: flex;
  gap: 1rem;
}

.security-checklist {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.checklist-item:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.check-icon {
  min-width: 40px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #999;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  transition: all 0.3s ease;
}

.check-icon.checked {
  background: #d1fae5;
  color: #10b981;
}

.check-content {
  flex: 1;
}

.check-content h4 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.check-content p {
  margin: 0;
  color: #999;
  font-size: 0.9rem;
}

.activity-summary {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 8px;
}

.activity-summary h3 {
  margin: 0 0 1rem 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.activity-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  border: 2px solid #e5e7eb;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #999;
  font-size: 0.9rem;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.link-card {
  padding: 1.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  cursor: pointer;
}

.link-card:hover {
  border-color: #667eea;
  background: #f0f4ff;
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.15);
}

.link-card i {
  font-size: 2rem;
  color: #667eea;
}

.link-card h3 {
  margin: 0;
  color: #333;
}

.link-card p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.privacy-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.privacy-card {
  padding: 1.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.privacy-card h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.privacy-card p {
  margin: 0 0 1rem 0;
  color: #666;
}

.mt-2 {
  margin-top: 1rem;
}

.mt-3 {
  margin-top: 1.5rem;
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .activity-stats {
    grid-template-columns: 1fr;
  }

  .dialog-actions {
    flex-direction: column;
  }
}
</style>

<style scoped>
.settings-section {
  padding: 2rem 0;
  border-bottom: 1px solid var(--gray-200);
}

.settings-section:last-child {
  border-bottom: none;
}

.settings-section h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--gray-900);
}

.section-description {
  color: var(--gray-600);
  margin-bottom: 1.5rem;
}

.security-status {
  margin-top: 1rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
}

.status-badge i {
  font-size: 1.25rem;
}

.status-success {
  background: #d1fae5;
  color: #065f46;
  border: 2px solid #10b981;
}

.status-warning {
  background: #fef3c7;
  color: #92400e;
  border: 2px solid #f59e0b;
}

.qr-code-section {
  margin-top: 2rem;
  padding: 2rem;
  background: var(--gray-50);
  border-radius: 12px;
  border: 2px solid var(--gray-200);
}

.qr-code-section h4 {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.qr-code-container {
  display: flex;
  justify-content: center;
  margin: 2rem 0;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.qr-code-image {
  max-width: 300px;
  width: 100%;
  height: auto;
  display: block;
}

.secret-key-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--gray-300);
}

.secret-key-display {
  display: flex;
  align-items: center;
  margin-top: 0.75rem;
}

.secret-key-display code {
  background: var(--gray-800);
  color: var(--white);
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 1.1rem;
  letter-spacing: 0.1em;
  flex: 1;
}

.verification-input-group {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.verification-input-group input {
  flex: 1;
  max-width: 200px;
  text-align: center;
  font-size: 1.5rem;
  letter-spacing: 0.5em;
  font-family: monospace;
}

.account-info {
  background: var(--gray-50);
  padding: 1.5rem;
  border-radius: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--gray-200);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 600;
  color: var(--gray-700);
}

.info-value {
  color: var(--gray-900);
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

@media (max-width: 768px) {
  .qr-code-image {
    max-width: 250px;
  }
  
  .verification-input-group {
    flex-direction: column;
  }
  
  .verification-input-group input {
    max-width: 100%;
  }
}
</style>
