import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
})

let csrfToken = null

function getCsrfToken() {
  if (csrfToken) return csrfToken
  
  const name = 'csrftoken'
  const cookies = document.cookie.split(';')
  
  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split('=')
    if (key === name) {
      csrfToken = decodeURIComponent(value)
      return csrfToken
    }
  }
  
  return null
}

api.interceptors.request.use(
  (config) => {
    if (['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
      const token = getCsrfToken()
      if (token) {
        config.headers['X-CSRFToken'] = token
      }
    }
    const accessToken = localStorage.getItem('access_token')
    if (accessToken) {
      config.headers['Authorization'] = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// FIXED: Remove automatic redirect on 401
// Let components handle authentication errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Just return the error, don't redirect
    // Components and router guards will handle it
    return Promise.reject(error)
  }
)

export const authAPI = {
  register(username, email, password, password2) {
    const payload = {
      username,
      email,
      password,
      password2
    }
    console.log('Sending registration payload:', payload)
    return api.post('/auth/register/', payload)
  },

  login(username, password, twoFactorToken = '') {
    return api.post('/auth/login/', {
      username,
      password,
      two_factor_token: twoFactorToken
    })
  },

  logout() {
    return api.post('/auth/logout/')
  },

  getCurrentUser() {
    return api.get('/auth/user/')
  },

  checkPasswordStrength(password) {
    return api.post('/auth/password-strength/', { password })
  },

  setup2FA(enable) {
    return api.post('/auth/2fa/setup/', { enable })
  },

  verify2FA(token, username) {
    return api.post('/auth/2fa/verify/', { 
      token,
      username
    })
  },

  changePassword(oldPassword, newPassword) {
    return api.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword
    })
  },

  // Profile Management
  getProfile() {
    return api.get('/auth/profile/')
  },

  updateProfile(data) {
    return api.put('/auth/profile/', data)
  },

  // Sessions Management
  getSessions() {
    return api.get('/auth/sessions/')
  },

  terminateSession(sessionId) {
    return api.delete(`/auth/sessions/${sessionId}/`)
  }
}

export const paymentAPI = {
  // Subscriptions (with Nepali prices in NPR)
  SUBSCRIPTION_PLANS: {
    free: {
      name: 'नि:शुल्क',
      price: 0,
      currency: 'NPR',
      features: ['10 notes', '5MB upload', 'Basic 2FA']
    },
    pro: {
      name: 'Pro',
      price: 599, // NPR equivalent (~$5 USD)
      currency: 'NPR',
      billingCycle: 'monthly',
      features: ['Unlimited notes', '50MB upload', 'Advanced 2FA', 'API access']
    },
    enterprise: {
      name: 'Enterprise',
      price: 1999, // NPR equivalent (~$15 USD)
      currency: 'NPR',
      billingCycle: 'monthly',
      features: ['Unlimited everything', '500MB upload', 'Premium 2FA', '24/7 support']
    }
  },

  // Get current subscription
  getCurrentSubscription() {
    return api.get('/subscriptions/')
  },

  // Upgrade plan
  upgradePlan(planType) {
    return api.post('/subscriptions/upgrade_plan/', { plan_type: planType })
  },

  // eSewa Payment Integration
  // Reference: https://esewa.com.np/developers
  initiateEsewaPayment(data) {
    // data should contain:
    // { amount: number, planType: string, orderId: string }
    const esewaData = {
      amt: data.amount,
      psc: 0,
      pdc: 0,
      txAmt: data.amount,
      tAmt: data.amount,
      pid: data.orderId, // Product/Order ID
      scd: process.env.VITE_ESEWA_MERCHANT_CODE || 'EPAYTEST', // Merchant code
      su: `${window.location.origin}/billing?status=success`, // Success URL
      fu: `${window.location.origin}/billing?status=failure` // Failure URL
    }
    
    // Generate hash (should be done on backend for security)
    return api.post('/payments/esewa/initiate/', {
      plan_type: data.planType,
      amount: data.amount,
      order_id: data.orderId,
      esewa_data: esewaData
    })
  },

  // Verify eSewa payment
  verifyEsewaPayment(refId, orderId) {
    return api.post('/payments/esewa/verify/', {
      ref_id: refId,
      order_id: orderId
    })
  },

  // Transactions
  getTransactions() {
    return api.get('/transactions/')
  },

  getTransaction(id) {
    return api.get(`/transactions/${id}/`)
  },

  // Billing History (with NPR currency)
  getBillingHistory() {
    return api.get('/billing/')
  },

  // Get billing summary with NPR prices
  getBillingSummary() {
    return api.get('/billing/summary/')
  },

  // eSewa Payment Methods
  initiateEsewaPayment(planId) {
    return api.post('/payments/esewa/initiate/', { plan_id: planId })
  },

  verifyPayment(transactionUUID) {
    return api.get(`/payments/verify/${transactionUUID}/`)
  },

  // API Keys
  getAPIKeys() {
    return api.get('/api-keys/')
  },

  createAPIKey(name) {
    return api.post('/api-keys/', { name })
  },

  revokeAPIKey(keyId) {
    return api.delete(`/api-keys/${keyId}/`)
  }
}

export const notesAPI = {
  getAllNotes() {
    return api.get('/notes/')
  },

  getNote(id) {
    return api.get(`/notes/${id}/`)
  },

  createNote(data) {
    return api.post('/notes/', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  updateNote(id, data) {
    return api.put(`/notes/${id}/`, data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  deleteNote(id) {
    return api.delete(`/notes/${id}/`)
  }
}

export default api
