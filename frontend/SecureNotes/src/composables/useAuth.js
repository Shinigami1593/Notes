import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'

export function useAuth() {
  const router = useRouter()
  const loading = ref(false)
  const error = ref(null)

  const register = async (username, email, password, password2) => {
    loading.value = true
    error.value = null

    try {
      console.log('Registering with:', { username, email, password, password2 })
      
      const response = await authAPI.register(username, email, password, password2)

      // Registration successful
      console.log('Registration successful:', response.data)
      
      // Redirect to login page
      router.push({
        path: '/login',
        query: { registered: 'true', username: username }
      })

      return response.data
    } catch (err) {
      console.error('Registration error:', err)
      console.error('Error response:', err.response?.data)
      error.value = err.response?.data || 'Registration failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  const login = async (username, password, twoFactorToken = '') => {
    loading.value = true
    error.value = null

    try {
      const response = await authAPI.login(username, password, twoFactorToken)
      
      if (response.data.two_factor_required) {
        return { twoFactorRequired: true }
      }

      if (response.data.password_expired) {
        return { passwordExpired: true }
      }

      // Login successful - redirect to dashboard
      router.push('/dashboard')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
      router.push('/login')
    } catch (err) {
      console.error('Logout error:', err)
      router.push('/login')
    }
  }

  return {
    register,
    login,
    logout,
    loading,
    error
  }
}