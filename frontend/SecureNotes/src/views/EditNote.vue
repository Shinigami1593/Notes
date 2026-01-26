<template>
  <div>
    <!-- Navigation Bar -->
    <AppNavbar />

    <div class="container">
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">
            <i class="bi bi-pencil-fill"></i>
            Edit Note
          </h2>
          <router-link to="/dashboard" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i>
            Back
          </router-link>
        </div>

        <!-- Note Metadata -->
        <div v-if="noteMetadata.created_at && !loadError" class="note-metadata">
          <div class="metadata-row">
            <span class="metadata-label">
              <i class="bi bi-calendar-event"></i>
              Created:
            </span>
            <span class="metadata-value">{{ formatDate(noteMetadata.created_at) }}</span>
          </div>
          <div class="metadata-row">
            <span class="metadata-label">
              <i class="bi bi-arrow-repeat"></i>
              Last Modified:
            </span>
            <span class="metadata-value">{{ formatDate(noteMetadata.modified_at) }}</span>
          </div>
          <div v-if="hasChanges" class="metadata-row unsaved">
            <span class="metadata-label">
              <i class="bi bi-exclamation-circle"></i>
              Status:
            </span>
            <span class="metadata-value">Unsaved Changes</span>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading && !formData.title" class="loading">
          <i class="bi bi-arrow-repeat"></i>
          <p>Loading note...</p>
        </div>

        <!-- Load Error -->
        <div v-else-if="loadError" class="alert alert-error">
          <i class="bi bi-exclamation-triangle-fill"></i>
          <span>{{ loadError }}</span>
        </div>

        <!-- Form -->
        <form v-else @submit.prevent="handleSubmit">
          <!-- Error Alert -->
          <div v-if="error" class="alert alert-error">
            <i class="bi bi-exclamation-triangle-fill"></i>
            <span>{{ error }}</span>
          </div>

          <!-- Success Alert -->
          <div v-if="success" class="alert alert-success">
            <i class="bi bi-check-circle-fill"></i>
            <span>Note updated successfully!</span>
          </div>

          <div class="form-group">
            <label for="title">
              <i class="bi bi-card-heading"></i>
              Title *
            </label>
            <input
              id="title"
              v-model="formData.title"
              type="text"
              class="form-control"
              :class="{ error: errors.title }"
              placeholder="Enter note title"
              required
              maxlength="200"
            />
            <span v-if="errors.title" class="error-text">
              {{ errors.title }}
            </span>
          </div>

          <div class="form-group">
            <label for="content">
              <i class="bi bi-journal-text"></i>
              Content *
            </label>
            <textarea
              id="content"
              v-model="formData.content"
              class="form-control"
              :class="{ error: errors.content }"
              placeholder="Enter note content"
              required
              rows="12"
            ></textarea>
            <span v-if="errors.content" class="error-text">
              {{ errors.content }}
            </span>
          </div>

          <!-- Current Attachment -->
          <div v-if="currentAttachment" class="form-group">
            <label>
              <i class="bi bi-paperclip"></i>
              Current Attachment
            </label>
            <div class="current-file">
              <div class="current-file-info">
                <i class="bi bi-file-earmark-fill"></i>
                <span>{{ currentAttachment.name }}</span>
              </div>
              <div class="current-file-actions">
                <a 
                  :href="currentAttachment.url" 
                  target="_blank" 
                  class="btn btn-secondary btn-sm"
                >
                  <i class="bi bi-eye-fill"></i>
                  View
                </a>
                <button 
                  type="button"
                  @click="removeCurrentAttachment"
                  class="btn btn-danger btn-sm"
                >
                  <i class="bi bi-trash-fill"></i>
                  Remove
                </button>
              </div>
            </div>
          </div>

          <!-- New Attachment Upload -->
          <div class="form-group">
            <label>
              <i class="bi bi-paperclip"></i>
              {{ currentAttachment ? 'Replace Attachment' : 'Add Attachment (Optional)' }}
            </label>
            <div class="file-input-wrapper">
              <input
                id="attachment"
                ref="fileInput"
                type="file"
                @change="handleFileSelect"
                accept=".txt,.pdf,.png,.jpg,.jpeg,.gif"
              />
              <label for="attachment" class="file-label">
                <i class="bi bi-cloud-upload-fill"></i>
                Choose File
              </label>
            </div>
            
            <div v-if="selectedFile" class="file-info">
              <div>
                <i class="bi bi-file-earmark-fill"></i>
                <strong>{{ selectedFile.name }}</strong> 
                ({{ formatFileSize(selectedFile.size) }})
              </div>
              <button 
                type="button" 
                @click="clearFile"
                class="btn btn-danger btn-sm"
              >
                <i class="bi bi-x-circle"></i>
                Remove
              </button>
            </div>
            
            <span class="form-help">
              <i class="bi bi-info-circle"></i>
              Allowed: .txt, .pdf, .png, .jpg, .jpeg, .gif (Max 5MB)
            </span>
            
            <span v-if="errors.attachment" class="error-text">
              {{ errors.attachment }}
            </span>
          </div>

          <div class="d-flex gap-2">
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="loading || !hasChanges"
            >
              <i class="bi" :class="loading ? 'bi-hourglass-split' : 'bi-check-circle-fill'"></i>
              {{ loading ? 'Saving...' : (hasChanges ? 'Save Changes' : 'No Changes') }}
            </button>
            <router-link to="/dashboard" class="btn btn-secondary">
              <i class="bi bi-x-circle"></i>
              Cancel
            </router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { notesAPI } from '../services/api'
import { useAuth } from '../composables/useAuth'
import AppNavbar from '../components/AppNavbar.vue'

const router = useRouter()
const route = useRoute()
const { logout, getCurrentUser } = useAuth()

const currentUser = ref(null)
const formData = ref({
  title: '',
  content: ''
})
const originalData = ref({
  title: '',
  content: ''
})
const noteMetadata = ref({
  created_at: null,
  modified_at: null
})
const currentAttachment = ref(null)
const selectedFile = ref(null)
const fileInput = ref(null)
const loading = ref(false)
const loadError = ref(null)
const error = ref(null)
const success = ref(false)
const errors = ref({})
const removeAttachment = ref(false)
const hasChanges = ref(false)

onMounted(async () => {
  currentUser.value = await getCurrentUser()
  await loadNote()
})

// Watch for changes in title and content
watch([() => formData.value.title, () => formData.value.content], () => {
  checkForChanges()
}, { deep: true })

const handleLogout = async () => {
  await logout()
}

const loadNote = async () => {
  try {
    loading.value = true
    const noteId = route.params.id
    const response = await notesAPI.getNote(noteId)
    const note = response.data
    
    // Store original data
    originalData.value.title = note.title
    originalData.value.content = note.content
    
    // Load into form
    formData.value.title = note.title
    formData.value.content = note.content
    
    // Store metadata
    noteMetadata.value.created_at = note.created_at
    noteMetadata.value.modified_at = note.modified_at
    
    if (note.attachment_url) {
      currentAttachment.value = {
        url: note.attachment_url,
        name: note.attachment.split('/').pop()
      }
    }
  } catch (err) {
    console.error('Failed to load note:', err)
    if (err.response?.status === 403) {
      loadError.value = 'Access denied. You do not have permission to edit this note.'
    } else {
      loadError.value = 'Failed to load note.'
    }
  } finally {
    loading.value = false
  }
}

const checkForChanges = () => {
  hasChanges.value = 
    formData.value.title !== originalData.value.title ||
    formData.value.content !== originalData.value.content ||
    removeAttachment.value
}

const removeCurrentAttachment = () => {
  currentAttachment.value = null
  removeAttachment.value = true
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  errors.value.attachment = null
  
  // Validate file size (5MB max)
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    errors.value.attachment = `File size exceeds 5MB limit (${formatFileSize(file.size)})`
    clearFile()
    return
  }
  
  // Validate file extension
  const allowedExtensions = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
  const fileExtension = file.name.split('.').pop().toLowerCase()
  
  if (!allowedExtensions.includes(fileExtension)) {
    errors.value.attachment = `File type ".${fileExtension}" not allowed. Allowed: ${allowedExtensions.join(', ')}`
    clearFile()
    return
  }
  
  // Validate MIME type for extra security
  const allowedMimes = {
    'txt': 'text/plain',
    'pdf': 'application/pdf',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif'
  }
  
  const expectedMime = allowedMimes[fileExtension]
  if (expectedMime && file.type && file.type !== expectedMime) {
    errors.value.attachment = `File MIME type does not match the extension. Expected: ${expectedMime}`
    clearFile()
    return
  }
  
  selectedFile.value = file
}

const clearFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
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

const handleSubmit = async () => {
  errors.value = {}
  error.value = null
  success.value = false
  
  if (!formData.value.title.trim()) {
    errors.value.title = 'Title is required'
    return
  }
  
  if (!formData.value.content.trim()) {
    errors.value.content = 'Content is required'
    return
  }
  
  try {
    loading.value = true
    
    const data = new FormData()
    data.append('title', formData.value.title.trim())
    data.append('content', formData.value.content.trim())
    
    if (selectedFile.value) {
      data.append('attachment', selectedFile.value)
    } 
    else if (removeAttachment.value && !currentAttachment.value) {
      data.append('attachment', '')
    }
    
    const noteId = route.params.id
    await notesAPI.updateNote(noteId, data)
    
    success.value = true
    
    setTimeout(() => {
      router.push('/dashboard')
    }, 1000)
    
  } catch (err) {
    console.error('Failed to update note:', err)
    
    if (err.response?.status === 403) {
      error.value = 'Access denied. You do not have permission to edit this note.'
    } else if (err.response?.data) {
      errors.value = err.response.data
      error.value = 'Please fix the errors below'
    } else {
      error.value = 'Failed to update note. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.note-metadata {
  background: #f0f4ff;
  border-left: 4px solid #667eea;
  padding: 1rem;
  margin-bottom: 1.5rem;
  border-radius: 0 8px 8px 0;
}

.metadata-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.metadata-row:last-child {
  margin-bottom: 0;
}

.metadata-label {
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metadata-value {
  color: #666;
  font-family: 'Monaco', 'Menlo', monospace;
}

.metadata-row.unsaved {
  background: #fef3c7;
  padding: 0.5rem;
  margin: 0 -0.5rem;
  border-radius: 4px;
}

.metadata-row.unsaved .metadata-label {
  color: #b45309;
}

.metadata-row.unsaved .metadata-value {
  color: #d97706;
  font-weight: 600;
}
</style>