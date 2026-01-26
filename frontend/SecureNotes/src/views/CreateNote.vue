<template>
  <div>
    <!-- Navigation Bar -->
    <AppNavbar />

    <div class="container">
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">
            <i class="bi bi-plus-circle-fill"></i>
            Create New Note
          </h2>
          <router-link to="/dashboard" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i>
            Back
          </router-link>
        </div>

        <!-- Error Alert -->
        <div v-if="error" class="alert alert-error">
          <i class="bi bi-exclamation-triangle-fill"></i>
          <span>{{ error }}</span>
        </div>

        <!-- Success Alert -->
        <div v-if="success" class="alert alert-success">
          <i class="bi bi-check-circle-fill"></i>
          <span>Note created successfully!</span>
        </div>

        <form @submit.prevent="handleSubmit">
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

          <div class="form-group">
            <label>
              <i class="bi bi-paperclip"></i>
              Attachment (Optional)
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
              :disabled="loading"
            >
              <i class="bi" :class="loading ? 'bi-hourglass-split' : 'bi-check-circle-fill'"></i>
              {{ loading ? 'Creating...' : 'Create Note' }}
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notesAPI } from '../services/api'
import { useAuth } from '../composables/useAuth'
import AppNavbar from '../components/AppNavbar.vue'

const router = useRouter()
const { logout, getCurrentUser } = useAuth()

const currentUser = ref(null)
const formData = ref({
  title: '',
  content: ''
})
const selectedFile = ref(null)
const fileInput = ref(null)
const loading = ref(false)
const error = ref(null)
const success = ref(false)
const errors = ref({})

onMounted(async () => {
  currentUser.value = await getCurrentUser()
})

const handleLogout = async () => {
  await logout()
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
    
    await notesAPI.createNote(data)
    
    success.value = true
    
    setTimeout(() => {
      router.push('/dashboard')
    }, 1000)
    
  } catch (err) {
    console.error('Failed to create note:', err)
    
    if (err.response?.data) {
      errors.value = err.response.data
      error.value = 'Please fix the errors below'
    } else {
      error.value = 'Failed to create note. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
<style></style>
