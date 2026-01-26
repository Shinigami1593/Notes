<template>
  <div class="transactions-container">
    <!-- Navigation -->
    <AppNavbar />

    <!-- Main Content -->
    <div class="container">
      <div class="transactions-grid">
        <!-- Sidebar Navigation -->
        <aside class="sidebar" role="navigation" aria-label="Payment sections">
          <nav class="section-nav">
            <button
              v-for="section in sections"
              :key="section.id"
              @click="activeSection = section.id"
              :class="['nav-item', { active: activeSection === section.id }]"
              :aria-current="activeSection === section.id ? 'page' : 'false'"
              :aria-label="section.label"
            >
              <i :class="section.icon"></i>
              {{ section.label }}
            </button>
          </nav>
        </aside>

        <!-- Main Content Area -->
        <main class="main-content">
          <!-- Header -->
          <div class="page-header">
            <h1><i class="bi bi-credit-card-fill"></i> Subscription & Billing</h1>
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

          <!-- Subscription Section -->
          <section v-if="activeSection === 'subscription'" class="section" aria-labelledby="subscription-heading">
            <h2 id="subscription-heading">Current Subscription Plan</h2>
            
            <div class="subscription-card">
              <div class="plan-info">
                <h3>{{ currentPlan.name }}</h3>
                <p class="plan-description">{{ currentPlan.description }}</p>
                <p class="plan-price">{{ formatPrice(currentPlan.price) }}<span>/month</span></p>
              </div>
              
              <div class="plan-features">
                <h4>Included Features</h4>
                <ul>
                  <li v-for="feature in currentPlan.features" :key="feature">
                    <i class="bi bi-check-circle-fill"></i>
                    {{ feature }}
                  </li>
                </ul>
              </div>

              <div class="plan-actions" v-if="currentPlan.id !== 'free'">
                <p class="renews-text">
                  <i class="bi bi-calendar-event"></i>
                  Renews on {{ formatDate(subscription.renews_at) }}
                </p>
              </div>
            </div>

            <div v-if="currentPlan.id !== 'pro'" class="upgrade-section">
              <h3>Upgrade to Pro</h3>
              <div class="plan-comparison">
                <div class="plan-card">
                  <div class="plan-header">
                    <h4>Free</h4>
                    <p class="price">$0<span>/mo</span></p>
                  </div>
                  <ul class="features-list">
                    <li><i class="bi bi-check"></i>Up to 50 notes</li>
                    <li><i class="bi bi-check"></i>Basic security</li>
                    <li><i class="bi bi-x"></i>File uploads</li>
                    <li><i class="bi bi-x"></i>Advanced search</li>
                  </ul>
                </div>

                <div class="plan-card pro">
                  <div class="best-choice">Best Choice</div>
                  <div class="plan-header">
                    <h4>Pro</h4>
                    <p class="price">$9.99<span>/mo</span></p>
                  </div>
                  <ul class="features-list">
                    <li><i class="bi bi-check"></i>Unlimited notes</li>
                    <li><i class="bi bi-check"></i>File uploads (500MB)</li>
                    <li><i class="bi bi-check"></i>Advanced search</li>
                    <li><i class="bi bi-check"></i>Priority support</li>
                  </ul>
                  <button @click="initiateEsewaPayment('pro')" class="btn btn-primary" :disabled="loading">
                    <i class="bi bi-wallet"></i> {{ loading ? 'Processing...' : 'Pay with eSewa' }}
                  </button>
                </div>

                <div class="plan-card">
                  <div class="plan-header">
                    <h4>Enterprise</h4>
                    <p class="price">Contact<span></span></p>
                  </div>
                  <ul class="features-list">
                    <li><i class="bi bi-check"></i>Custom limits</li>
                    <li><i class="bi bi-check"></i>Team management</li>
                    <li><i class="bi bi-check"></i>API access</li>
                    <li><i class="bi bi-check"></i>Dedicated support</li>
                  </ul>
                  <button class="btn btn-outline">Contact Sales</button>
                </div>
              </div>
            </div>
          </section>

          <!-- Transactions Section -->
          <section v-if="activeSection === 'transactions'" class="section" aria-labelledby="transactions-heading">
            <h2 id="transactions-heading">Transaction History</h2>
            
            <div class="filters">
              <div class="filter-group">
                <label for="status-filter">Filter by Status:</label>
                <select v-model="selectedStatus" id="status-filter" class="form-control">
                  <option value="">All Transactions</option>
                  <option value="completed">Completed</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                  <option value="refunded">Refunded</option>
                </select>
              </div>
            </div>

            <div v-if="loadingTransactions" class="loading">
              <p>Loading transactions...</p>
            </div>

            <div v-else-if="filteredTransactions.length === 0" class="no-data">
              <i class="bi bi-inbox"></i>
              <p>No transactions found</p>
            </div>

            <div v-else class="transactions-table-wrapper">
              <table class="transactions-table" role="table" aria-label="Transaction history">
                <thead>
                  <tr>
                    <th scope="col">Date</th>
                    <th scope="col">Amount</th>
                    <th scope="col">Description</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="transaction in filteredTransactions" :key="transaction.id">
                    <td>{{ formatDate(transaction.created_at) }}</td>
                    <td class="amount">{{ formatPrice(transaction.amount / 100) }}</td>
                    <td>{{ transaction.description }}</td>
                    <td>
                      <span :class="['status-badge', `status-${transaction.status}`]">
                        {{ capitalizeStatus(transaction.status) }}
                      </span>
                    </td>
                    <td>
                      <button 
                        @click="viewTransactionDetails(transaction)"
                        class="btn btn-sm btn-outline"
                        :aria-label="`View details for transaction ${transaction.id}`"
                      >
                        <i class="bi bi-eye"></i>
                        View
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- Billing Section -->
          <section v-if="activeSection === 'billing'" class="section" aria-labelledby="billing-heading">
            <h2 id="billing-heading">Billing Information</h2>
            
            <div class="billing-card">
              <h3>Billing Details</h3>
              <div class="billing-info">
                <div class="info-row">
                  <span class="label">Current Plan:</span>
                  <span class="value">{{ subscription.plan_type }} - {{ formatPrice(subscription.plan_price) }}/month</span>
                </div>
                <div class="info-row">
                  <span class="label">Billing Cycle:</span>
                  <span class="value">Monthly</span>
                </div>
                <div class="info-row">
                  <span class="label">Next Billing Date:</span>
                  <span class="value">{{ formatDate(subscription.renews_at) }}</span>
                </div>
                <div class="info-row">
                  <span class="label">Subscription Status:</span>
                  <span :class="['status', subscription.is_active ? 'active' : 'inactive']">
                    {{ subscription.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="loadingBilling" class="loading">
              <p>Loading billing history...</p>
            </div>

            <div v-else-if="billingHistory.length === 0" class="no-data">
              <p>No billing history available</p>
            </div>

            <div v-else class="billing-history">
              <h3>Billing History</h3>
              <div class="history-list">
                <div v-for="bill in billingHistory" :key="bill.id" class="history-item" role="article">
                  <div class="item-info">
                    <h4>{{ bill.event_type }}</h4>
                    <p class="date">{{ formatDate(bill.created_at) }}</p>
                  </div>
                  <div class="item-amount" :class="{ positive: bill.amount > 0, negative: bill.amount < 0 }">
                    {{ formatPrice(Math.abs(bill.amount) / 100) }}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- eSewa Payment Section -->
          <section v-if="activeSection === 'methods'" class="section" aria-labelledby="methods-heading">
            <h2 id="methods-heading">Payment Method - eSewa</h2>
            
            <div class="esewa-info">
              <div class="info-card">
                <i class="bi bi-shield-check"></i>
                <h3>Secure Payment with eSewa</h3>
                <p>Fast and secure online payment system trusted in Nepal</p>
              </div>
              <div class="payment-instructions">
                <h4>How to Pay with eSewa</h4>
                <ol>
                  <li>Click the "Upgrade to Pro" button in the Subscription section</li>
                  <li>You'll be redirected to eSewa payment gateway</li>
                  <li>Complete your payment using eSewa wallet or bank</li>
                  <li>Your subscription will be activated upon successful payment</li>
                </ol>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>

    <!-- Payment Processing Modal -->
    <div v-if="showPaymentForm" class="modal-overlay" @click="showPaymentForm = false">
      <div class="modal" @click.stop>
        <button @click="showPaymentForm = false" class="modal-close" aria-label="Close">
          <i class="bi bi-x"></i>
        </button>
        <h3>Processing Payment</h3>
        <div class="modal-loading">
          <div class="spinner"></div>
          <p>Redirecting to eSewa...</p>
        </div>
      </div>
    </div>

    <!-- Transaction Details Modal -->
    <div v-if="showTransactionModal" class="modal-overlay" @click="showTransactionModal = false">
      <div class="modal" @click.stop>
        <button @click="showTransactionModal = false" class="modal-close" aria-label="Close">
          <i class="bi bi-x"></i>
        </button>
        <h3>Transaction Details</h3>
        <div v-if="selectedTransaction" class="transaction-details">
          <div class="detail-row">
            <span class="label">Transaction ID:</span>
            <span class="value">{{ selectedTransaction.id }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Amount:</span>
            <span class="value">{{ formatPrice(selectedTransaction.amount / 100) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Status:</span>
            <span :class="['status-badge', `status-${selectedTransaction.status}`]">
              {{ capitalizeStatus(selectedTransaction.status) }}
            </span>
          </div>
          <div class="detail-row">
            <span class="label">Date:</span>
            <span class="value">{{ formatDate(selectedTransaction.created_at) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Description:</span>
            <span class="value">{{ selectedTransaction.description }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI, notesAPI, paymentAPI } from '../services/api'
import AppNavbar from '../components/AppNavbar.vue'

const router = useRouter()
const activeSection = ref('subscription')
const loading = ref(false)
const loadingTransactions = ref(false)
const loadingBilling = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const selectedStatus = ref('')
const showPaymentForm = ref(false)
const showTransactionModal = ref(false)
const selectedTransaction = ref(null)

const sections = [
  { id: 'subscription', label: 'Subscription', icon: 'bi bi-star-fill' },
  { id: 'transactions', label: 'Transactions', icon: 'bi bi-receipt' },
  { id: 'billing', label: 'Billing', icon: 'bi bi-credit-card' },
  { id: 'methods', label: 'Payment Methods', icon: 'bi bi-wallet2' },
]

const plans = {
  free: {
    id: 'free',
    name: 'Free',
    description: 'For personal use',
    price: 0,
    features: ['Up to 50 notes', 'Basic security', 'Text editing only', 'Standard support']
  },
  pro: {
    id: 'pro',
    name: 'Professional',
    description: 'For power users',
    price: 9.99,
    features: ['Unlimited notes', 'File uploads (500MB)', 'Advanced search', 'Priority support', 'API access']
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For organizations',
    price: 0,
    features: ['Custom limits', 'Team management', 'API access', 'Dedicated support']
  }
}

const subscription = ref({
  plan_type: 'free',
  plan_price: 0,
  renews_at: new Date(),
  is_active: true
})

const currentPlan = computed(() => plans[subscription.value.plan_type] || plans.free)

const transactions = ref([])
const filteredTransactions = computed(() => {
  return selectedStatus.value 
    ? transactions.value.filter(t => t.status === selectedStatus.value)
    : transactions.value
})

const billingHistory = ref([])

onMounted(async () => {
  await loadSubscription()
  await loadTransactions()
  await loadBillingHistory()
})

const loadSubscription = async () => {
  try {
    // This would call the actual subscription endpoint
    // const response = await notesAPI.getSubscription()
    // subscription.value = response.data
    subscription.value = {
      plan_type: 'free',
      plan_price: 0,
      renews_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      is_active: true
    }
  } catch (error) {
    errorMessage.value = 'Failed to load subscription'
  }
}

const loadTransactions = async () => {
  loadingTransactions.value = true
  try {
    // This would call the transactions endpoint
    // const response = await notesAPI.getTransactions()
    // transactions.value = response.data
    transactions.value = []
  } catch (error) {
    errorMessage.value = 'Failed to load transactions'
  } finally {
    loadingTransactions.value = false
  }
}

const loadBillingHistory = async () => {
  loadingBilling.value = true
  try {
    // This would call the billing history endpoint
    // const response = await notesAPI.getBillingHistory()
    // billingHistory.value = response.data
    billingHistory.value = []
  } catch (error) {
    errorMessage.value = 'Failed to load billing history'
  } finally {
    loadingBilling.value = false
  }
}

const upgradePlan = async (planId) => {
  loading.value = true
  try {
    // This would call the upgrade endpoint
    // await notesAPI.upgradePlan(planId)
    successMessage.value = 'Plan upgrade initiated'
    setTimeout(() => successMessage.value = '', 3000)
  } catch (error) {
    errorMessage.value = 'Failed to upgrade plan'
  } finally {
    loading.value = false
  }
}

const addPaymentMethod = async () => {
  loading.value = true
  try {
    // This would call the add payment method endpoint
    // await notesAPI.addPaymentMethod(newCard.value)
    successMessage.value = 'Payment method added'
    showPaymentForm.value = false
    newCard.value = { name: '', number: '', expiry: '', cvc: '' }
    // await loadPaymentMethods()
  } catch (error) {
    errorMessage.value = 'Failed to add payment method'
  } finally {
    loading.value = false
  }
}

const viewTransactionDetails = (transaction) => {
  selectedTransaction.value = transaction
  showTransactionModal.value = true
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

const formatPrice = (amount) => {
  return new Intl.NumberFormat('ne-NP', {
    style: 'currency',
    currency: 'NPR'
  }).format(amount)
}

const capitalizeStatus = (status) => {
  return status.charAt(0).toUpperCase() + status.slice(1)
}

const initiateEsewaPayment = async (planId) => {
  loading.value = true
  showPaymentForm.value = true
  try {
    // Call backend to initiate eSewa payment
    const response = await paymentAPI.initiateEsewaPayment(planId)
    
    if (response.data.success) {
      const { formData, esewaUrl } = response.data.data
      
      // Create and submit a hidden form to redirect to eSewa
      const form = document.createElement('form')
      form.method = 'POST'
      form.action = esewaUrl
      
      // Add all form fields
      Object.entries(formData).forEach(([key, value]) => {
        const input = document.createElement('input')
        input.type = 'hidden'
        input.name = key
        input.value = value
        form.appendChild(input)
      })
      
      document.body.appendChild(form)
      form.submit()
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.message || 'Failed to initiate payment'
    showPaymentForm.value = false
    console.error('Payment error:', error)
  } finally {
    loading.value = false
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
.transactions-container {
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

.container {
  max-width: 1400px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.transactions-grid {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 2rem;
}

.sidebar {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  height: fit-content;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.section-nav {
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

.main-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.page-header h1 {
  margin: 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section {
  display: block;
}

.section h2 {
  margin-bottom: 1.5rem;
  color: #333;
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

.subscription-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.plan-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
}

.plan-description {
  margin: 0 0 1rem 0;
  opacity: 0.9;
}

.plan-price {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
}

.plan-price span {
  font-size: 1rem;
  opacity: 0.8;
}

.plan-features {
  margin-top: 1.5rem;
}

.plan-features h4 {
  margin-bottom: 0.75rem;
}

.plan-features ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.upgrade-section {
  margin-top: 2rem;
}

.plan-comparison {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.plan-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  position: relative;
  transition: all 0.3s ease;
}

.plan-card:hover {
  border-color: #667eea;
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.15);
}

.plan-card.pro {
  border-color: #667eea;
  background: #f0f4ff;
  transform: scale(1.05);
}

.best-choice {
  position: absolute;
  top: -12px;
  left: 20px;
  background: #667eea;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: bold;
}

.plan-header {
  margin-bottom: 1rem;
}

.plan-header h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.price {
  margin: 0;
  font-size: 1.5rem;
  font-weight: bold;
  color: #667eea;
}

.price span {
  font-size: 0.9rem;
  opacity: 0.8;
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.features-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
}

.features-list i {
  color: #10b981;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 600;
  color: #333;
}

.form-control {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.transactions-table-wrapper {
  overflow-x: auto;
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.transactions-table thead {
  background: #f9fafb;
}

.transactions-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e5e7eb;
}

.transactions-table td {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.amount {
  font-weight: 600;
  color: #667eea;
}

.status-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-failed {
  background: #fee2e2;
  color: #991b1b;
}

.status-refunded {
  background: #e0e7ff;
  color: #3730a3;
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

.btn-outline {
  background: transparent;
  border: 2px solid #667eea;
  color: #667eea;
}

.btn-outline:hover {
  background: #f0f4ff;
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

.billing-card {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.billing-card h3 {
  margin-top: 0;
  color: #333;
}

.billing-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.label {
  font-weight: 600;
  color: #666;
}

.value {
  color: #333;
}

.status {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status.active {
  background: #d1fae5;
  color: #065f46;
}

.status.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.billing-history {
  margin-top: 2rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s ease;
}

.history-item:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.item-info h4 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.item-info .date {
  margin: 0;
  color: #999;
  font-size: 0.9rem;
}

.item-amount {
  font-weight: 600;
  font-size: 1.1rem;
}

.item-amount.positive {
  color: #10b981;
}

.item-amount.negative {
  color: #ef4444;
}

.payment-methods {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.method-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.method-card:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.method-icon {
  font-size: 2rem;
  color: #667eea;
  min-width: 50px;
  text-align: center;
}

.method-info {
  flex: 1;
}

.method-info h4 {
  margin: 0;
  color: #333;
}

.method-info p {
  margin: 0.25rem 0 0 0;
  color: #999;
  font-size: 0.9rem;
}

.method-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.badge {
  display: inline-block;
  background: #d1fae5;
  color: #065f46;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.add-payment {
  margin-top: 2rem;
}

.add-payment h3 {
  margin-bottom: 1rem;
  color: #333;
}

.payment-form {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.loading,
.no-data {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.no-data i {
  font-size: 3rem;
  color: #ccc;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
}

.modal-close:hover {
  color: #333;
}

.transaction-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

/* eSewa Payment Styles */
.esewa-info {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.info-card i {
  font-size: 3rem;
}

.info-card h3 {
  margin: 0;
  font-size: 1.5rem;
}

.info-card p {
  margin: 0;
  opacity: 0.9;
}

.payment-instructions {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.payment-instructions h4 {
  margin-top: 0;
  color: #333;
}

.payment-instructions ol {
  margin: 0;
  padding-left: 1.5rem;
  color: #666;
}

.payment-instructions li {
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

.modal-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .transactions-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
  
  .plan-card.pro {
    transform: scale(1);
  }
}
</style>
