<template>
  <div class="profile-container">
    <!-- Navigation -->
    <AppNavbar />

    <!-- Main Content -->
    <div class="container">
      <div class="profile-grid">
        <!-- Sidebar Navigation -->
        <aside class="profile-sidebar" role="navigation" aria-label="Profile settings">
          <nav class="settings-nav">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="['nav-item', { active: activeTab === tab.id }]"
              :aria-current="activeTab === tab.id ? 'page' : 'false'"
              :aria-label="tab.label"
            >
              <i :class="tab.icon"></i>
              {{ tab.label }}
            </button>
          </nav>
        </aside>

        <!-- Main Content Area -->
        <main class="profile-main">
          <!-- Header -->
          <div class="profile-header">
            <h1><i class="bi bi-person-fill"></i> My Profile</h1>
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

          <!-- Profile Tab -->
          <section v-if="activeTab === 'profile'" class="tab-content" aria-labelledby="profile-tab">
            <h2 id="profile-tab">Personal Information</h2>
            <form @submit.prevent="updateProfile" class="profile-form">
              <div class="form-row">
                <div class="form-group">
                  <label for="username">
                    <i class="bi bi-person-fill"></i>
                    Username
                  </label>
                  <input
                    id="username"
                    v-model="profile.username"
                    type="text"
                    class="form-control"
                    disabled
                    aria-readonly="true"
                  />
                  <small>Username cannot be changed</small>
                </div>

                <div class="form-group">
                  <label for="email">
                    <i class="bi bi-envelope-fill"></i>
                    Email
                  </label>
                  <input
                    id="email"
                    v-model="profile.email"
                    type="email"
                    class="form-control"
                    disabled
                    aria-readonly="true"
                  />
                  <small>Email is associated with your account</small>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="bio">
                    <i class="bi bi-chat-left-text"></i>
                    Bio
                  </label>
                  <textarea
                    id="bio"
                    v-model="profileData.bio"
                    class="form-control"
                    placeholder="Tell us about yourself"
                    maxlength="500"
                    rows="4"
                    aria-describedby="bio-help"
                  ></textarea>
                  <small id="bio-help">{{ profileData.bio.length }}/500 characters</small>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="phone">
                    <i class="bi bi-telephone-fill"></i>
                    Phone Number
                  </label>
                  <input
                    id="phone"
                    v-model="profileData.phone_number"
                    type="tel"
                    class="form-control"
                    placeholder="(123) 456-7890"
                    aria-describedby="phone-help"
                  />
                  <small id="phone-help">Optional - helps us contact you</small>
                </div>

                <div class="form-group">
                  <label for="dob">
                    <i class="bi bi-calendar-event"></i>
                    Date of Birth
                  </label>
                  <input
                    id="dob"
                    v-model="profileData.date_of_birth"
                    type="date"
                    class="form-control"
                    aria-describedby="dob-help"
                  />
                  <small id="dob-help">Optional - for age verification</small>
                </div>
              </div>

              <div class="form-actions">
                <button type="submit" class="btn btn-primary" :disabled="loading">
                  <i :class="loading ? 'bi-hourglass-split' : 'bi-check-circle'"></i>
                  {{ loading ? 'Saving...' : 'Save Changes' }}
                </button>
              </div>
            </form>
          </section>

          <!-- Privacy Tab -->
          <section v-if="activeTab === 'privacy'" class="tab-content" aria-labelledby="privacy-tab">
            <h2 id="privacy-tab">Privacy & Visibility Settings</h2>
            <div class="settings-group">
              <div class="setting-item">
                <div class="setting-header">
                  <h3>Profile Visibility</h3>
                  <p>Control who can see your profile</p>
                </div>
                <select v-model="profileData.profile_visibility" class="form-control" aria-label="Profile visibility">
                  <option value="private">Private - Only you can see</option>
                  <option value="friends">Friends Only</option>
                  <option value="public">Public - Everyone can see</option>
                </select>
              </div>

              <div class="setting-item">
                <div class="setting-header">
                  <h3>Show Email</h3>
                  <p>Allow others to see your email address</p>
                </div>
                <label class="checkbox-wrapper">
                  <input v-model="profileData.show_email" type="checkbox" />
                  <span>Display email on profile</span>
                </label>
              </div>

              <div class="setting-item">
                <div class="setting-header">
                  <h3>Activity Status</h3>
                  <p>Show when you were last active</p>
                </div>
                <label class="checkbox-wrapper">
                  <input v-model="profileData.show_activity" type="checkbox" />
                  <span>Display my activity status</span>
                </label>
              </div>
            </div>

            <div class="form-actions">
              <button @click="updateProfile" class="btn btn-primary" :disabled="loading">
                <i :class="loading ? 'bi-hourglass-split' : 'bi-check-circle'"></i>
                {{ loading ? 'Saving...' : 'Save Privacy Settings' }}
              </button>
            </div>
          </section>

          <!-- Notifications Tab -->
          <section v-if="activeTab === 'notifications'" class="tab-content" aria-labelledby="notifications-tab">
            <h2 id="notifications-tab">Notification Preferences</h2>
            <div class="settings-group">
              <div class="setting-item">
                <div class="setting-header">
                  <h3>Login Attempt Notifications</h3>
                  <p>Get notified of suspicious login attempts</p>
                </div>
                <label class="checkbox-wrapper">
                  <input v-model="profileData.notify_login_attempts" type="checkbox" />
                  <span>Notify me of login attempts</span>
                </label>
              </div>

              <div class="setting-item">
                <div class="setting-header">
                  <h3>Password Change Notifications</h3>
                  <p>Get notified when your password is changed</p>
                </div>
                <label class="checkbox-wrapper">
                  <input v-model="profileData.notify_password_changes" type="checkbox" />
                  <span>Notify me of password changes</span>
                </label>
              </div>

              <div class="setting-item">
                <div class="setting-header">
                  <h3>2FA Changes</h3>
                  <p>Get notified of 2FA setup or changes</p>
                </div>
                <label class="checkbox-wrapper">
                  <input v-model="profileData.notify_2fa_changes" type="checkbox" />
                  <span>Notify me of 2FA changes</span>
                </label>
              </div>

              <div class="setting-item">
                <div class="setting-header">
                  <h3>New Notes Reminders</h3>
                  <p>Get reminders about new notes</p>
                </div>
                <label class="checkbox-wrapper">
                  <input v-model="profileData.notify_new_notes" type="checkbox" />
                  <span>Remind me about new notes</span>
                </label>
              </div>
            </div>

            <div class="form-actions">
              <button @click="updateProfile" class="btn btn-primary" :disabled="loading">
                <i :class="loading ? 'bi-hourglass-split' : 'bi-check-circle'"></i>
                {{ loading ? 'Saving...' : 'Save Notification Settings' }}
              </button>
            </div>
          </section>

          <!-- Sessions Tab -->
          <section v-if="activeTab === 'sessions'" class="tab-content" aria-labelledby="sessions-tab">
            <h2 id="sessions-tab">Active Sessions</h2>
            <p class="section-description">Manage your active login sessions across all devices</p>
            
            <div v-if="loadingSessions" class="loading">
              <p>Loading sessions...</p>
            </div>
            
            <div v-else-if="sessions.length === 0" class="no-data">
              <p>No active sessions found</p>
            </div>

            <div v-else class="sessions-list">
              <div v-for="session in sessions" :key="session.id" class="session-item" role="article">
                <div class="session-info">
                  <div class="session-device">
                    <i class="bi bi-laptop"></i>
                    <div>
                      <h4>{{ session.device_name || 'Unknown Device' }}</h4>
                      <p>{{ session.session_type }} • {{ session.ip_address }}</p>
                    </div>
                  </div>
                  <div class="session-time">
                    <small>Last active: {{ formatDate(session.last_activity) }}</small>
                  </div>
                </div>
                <button
                  @click="terminateSession(session.id)"
                  class="btn btn-danger btn-sm"
                  aria-label="Terminate this session"
                >
                  <i class="bi bi-x-circle"></i>
                  Terminate
                </button>
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
import { authAPI, notesAPI } from '../services/api'
import AppNavbar from '../components/AppNavbar.vue'

const router = useRouter()
const activeTab = ref('profile')
const loading = ref(false)
const loadingSessions = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const profile = ref({
  username: '',
  email: '',
  bio: '',
  phone_number: '',
  date_of_birth: '',
  profile_visibility: 'private',
  show_email: false,
  show_activity: false,
  notify_login_attempts: true,
  notify_password_changes: true,
  notify_2fa_changes: true,
  notify_new_notes: false,
})

const profileData = ref({
  bio: '',
  phone_number: '',
  date_of_birth: '',
  profile_visibility: 'private',
  show_email: false,
  show_activity: false,
  notify_login_attempts: true,
  notify_password_changes: true,
  notify_2fa_changes: true,
  notify_new_notes: false,
})

const sessions = ref([])

const tabs = [
  { id: 'profile', label: 'Personal Info', icon: 'bi bi-person-fill' },
  { id: 'privacy', label: 'Privacy', icon: 'bi bi-lock-fill' },
  { id: 'notifications', label: 'Notifications', icon: 'bi bi-bell-fill' },
  { id: 'sessions', label: 'Sessions', icon: 'bi bi-cloud-check' },
]

onMounted(async () => {
  await loadProfile()
  await loadSessions()
})

const loadProfile = async () => {
  try {
    // Fetch profile data from backend
    const response = await authAPI.getProfile()
    const userData = response.data
    
    // Update profile with backend data
    profile.value = {
      id: userData.id,
      username: userData.username,
      email: userData.email,
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
      avatar_url: userData.avatar_url || '',
      bio: userData.bio || '',
      phone_number: userData.phone_number || '',
      date_of_birth: userData.date_of_birth || '',
      profile_visibility: userData.profile_visibility || 'private',
      show_email: userData.show_email || false,
      show_activity: userData.show_activity || false,
      notify_login_attempts: userData.notify_login_attempts !== false,
      notify_password_changes: userData.notify_password_changes !== false,
      notify_2fa_changes: userData.notify_2fa_changes !== false,
      notify_new_notes: userData.notify_new_notes || false,
    }
    
    // Copy to form data
    profileData.value = { ...profile.value }
  } catch (error) {
    console.error('Error loading profile:', error)
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      router.push('/login')
    } else {
      errorMessage.value = 'Failed to load profile. Please try again.'
    }
  }
}

const updateProfile = async () => {
  loading.value = true
  try {
    // Call API to update profile
    await authAPI.updateProfile(profileData.value)
    successMessage.value = 'Profile updated successfully'
    setTimeout(() => successMessage.value = '', 3000)
  } catch (error) {
    console.error('Error updating profile:', error)
    errorMessage.value = 'Failed to update profile'
  } finally {
    loading.value = false
  }
}

const loadSessions = async () => {
  loadingSessions.value = true
  try {
    // This would call the sessions endpoint
    // const response = await authAPI.getSessions()
    // sessions.value = response.data
    sessions.value = []
  } catch (error) {
    console.error('Error loading sessions:', error)
  } finally {
    loadingSessions.value = false
  }
}

const terminateSession = async (sessionId) => {
  if (!confirm('Are you sure you want to terminate this session?')) return
  
  try {
    // await authAPI.terminateSession(sessionId)
    await loadSessions()
    successMessage.value = 'Session terminated'
  } catch (error) {
    errorMessage.value = 'Failed to terminate session'
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Unknown'
  const options = { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  }
  return new Date(dateString).toLocaleDateString('en-US', options)
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
.profile-container {
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

.profile-grid {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.profile-sidebar {
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

.profile-main {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.profile-header h1 {
  margin: 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
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

.tab-content {
  display: block;
}

.tab-content h2 {
  margin-bottom: 1.5rem;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
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

.form-control:disabled {
  background: #f9fafb;
  cursor: not-allowed;
  opacity: 0.6;
}

.form-control small,
.form-group small {
  color: #999;
  font-size: 0.85rem;
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

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.settings-group {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.setting-item {
  padding: 1.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.setting-item:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.setting-header {
  margin-bottom: 1rem;
}

.setting-header h3 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.setting-header p {
  margin: 0;
  color: #999;
  font-size: 0.9rem;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-wrapper input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.section-description {
  color: #666;
  margin-bottom: 1.5rem;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.session-item {
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.session-info {
  flex: 1;
}

.session-device {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.session-device i {
  font-size: 1.5rem;
  color: #667eea;
}

.session-device h4 {
  margin: 0;
  color: #333;
}

.session-device p {
  margin: 0;
  color: #999;
  font-size: 0.9rem;
}

.session-time small {
  color: #999;
}

.loading,
.no-data {
  text-align: center;
  padding: 2rem;
  color: #666;
}

@media (max-width: 768px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .profile-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .session-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
