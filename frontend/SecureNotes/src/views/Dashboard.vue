<template>
  <div class="dashboard-container">
    <AppNavbar />

    <div class="content">
      <!-- Welcome & Security Status -->
      <div class="welcome-card">
        <h2>Welcome back! 👋</h2>
        <p>Your account is secure and ready to use.</p>
        
        <div class="security-status">
          <div class="status-item" :class="twoFactorEnabled ? 'enabled' : 'disabled'">
            <i class="bi" :class="twoFactorEnabled ? 'bi-shield-fill-check' : 'bi-shield-fill-x'"></i>
            <div>
              <h3>Two-Factor Authentication</h3>
              <p v-if="twoFactorEnabled">Enabled - Your account has extra protection</p>
              <p v-else>Disabled - Enable 2FA for better security</p>
            </div>
            <router-link v-if="!twoFactorEnabled" to="/settings/2fa" class="btn btn-primary">
              Enable 2FA
            </router-link>
          </div>
        </div>
      </div>

      <!-- Create Note Button -->
      <div class="create-note-banner">
        <div class="banner-content">
          <h3><i class="bi bi-plus-circle-fill"></i> Ready to create a new note?</h3>
          <p>Organize your thoughts and keep important information secure</p>
        </div>
        <router-link to="/notes/create" class="btn btn-primary btn-lg">
          <i class="bi bi-plus-lg"></i> Create New Note
        </router-link>
      </div>

      <!-- Notes List -->
      <div class="notes-section">
        <h3><i class="bi bi-file-text"></i> Your Notes ({{ notes.length }})</h3>
        
        <div v-if="loadingNotes" class="loading">
          <p>Loading notes...</p>
        </div>

        <div v-else-if="notes.length === 0" class="no-notes">
          <p>No notes yet. Create one to get started!</p>
        </div>

        <div v-else class="notes-grid">
          <div v-for="note in notes" :key="note.id" class="note-card">
            <div class="note-header">
              <h4>{{ note.title }}</h4>
              <div class="note-actions">
                <router-link :to="`/notes/${note.id}/edit`" class="btn-icon">
                  <i class="bi bi-pencil"></i>
                </router-link>
                <button @click="handleDeleteNote(note.id)" class="btn-icon btn-danger">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
            <p class="note-content">{{ truncateContent(note.content) }}</p>
            <p class="note-meta">{{ formatDate(note.created_at) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'
import { notesAPI } from '../services/api'
import AppNavbar from '../components/AppNavbar.vue'

const router = useRouter()
const twoFactorEnabled = ref(false)
const notes = ref([])
const loadingNotes = ref(false)

onMounted(async () => {
  try {
    const response = await authAPI.getCurrentUser()
    twoFactorEnabled.value = response.data.two_factor_enabled
  } catch (error) {
    console.error('Error loading user data:', error)
    router.push('/login')
  }
  
  await loadNotes()
})

const loadNotes = async () => {
  loadingNotes.value = true
  try {
    const response = await notesAPI.getAllNotes()
    notes.value = response.data
  } catch (error) {
    console.error('Error loading notes:', error)
  } finally {
    loadingNotes.value = false
  }
}

const handleDeleteNote = async (id) => {
  if (!confirm('Are you sure you want to delete this note? This action cannot be undone.')) {
    return
  }
  
  try {
    await notesAPI.deleteNote(id)
    await loadNotes()
  } catch (error) {
    console.error('Error deleting note:', error)
    alert('Failed to delete note. Please try again.')
  }
}

const truncateContent = (content) => {
  const maxLength = 150
  if (content.length > maxLength) {
    return content.substring(0, maxLength) + '...'
  }
  return content
}

const formatDate = (dateString) => {
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }
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
.dashboard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.navbar {
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 1rem 0;
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-content h1 {
  margin: 0;
  color: #667eea;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-links {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.nav-link {
  padding: 0.5rem 1rem;
  text-decoration: none;
  color: #666;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.nav-link:hover {
  background: #f0f0f0;
  color: #667eea;
}

.btn-logout {
  padding: 0.5rem 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-logout:hover {
  background: #dc2626;
  transform: translateY(-2px);
}

.content {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.welcome-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.welcome-card h2 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.welcome-card > p {
  margin: 0 0 2rem 0;
  color: #666;
}

.security-status {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 8px;
  border: 2px solid;
}

.status-item.enabled {
  background: #d1fae5;
  border-color: #10b981;
}

.status-item.disabled {
  background: #fee2e2;
  border-color: #ef4444;
}

.status-item > i {
  font-size: 2.5rem;
}

.status-item.enabled > i {
  color: #10b981;
}

.status-item.disabled > i {
  color: #ef4444;
}

.status-item > div {
  flex: 1;
}

.status-item h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
}

.status-item p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
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

/* Create Note Banner */
.create-note-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.banner-content h3 {
  margin: 0 0 0.5rem 0;
  color: white;
  font-size: 1.3rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.banner-content p {
  margin: 0;
  color: rgba(255,255,255,0.9);
}

.btn-lg {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  white-space: nowrap;
}

/* Notes Section */
.notes-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.notes-section h3 {
  margin: 0 0 1.5rem 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading, .no-notes {
  text-align: center;
  color: #666;
  padding: 2rem;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.note-card {
  background: #f9fafb;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.note-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.note-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
}

.note-header h4 {
  margin: 0;
  color: #333;
  flex: 1;
  word-break: break-word;
}

.note-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #667eea;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-icon:hover {
  background: #e5e7eb;
  color: #5568d3;
}

.btn-icon.btn-danger {
  color: #ef4444;
}

.btn-icon.btn-danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.note-content {
  margin: 0 0 1rem 0;
  color: #666;
  line-height: 1.6;
  word-break: break-word;
}

.note-meta {
  margin: 0;
  color: #999;
  font-size: 0.85rem;
}
</style>