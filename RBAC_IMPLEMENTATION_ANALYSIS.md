# RBAC (Role-Based Access Control) Implementation Analysis

## Executive Summary

**Status:** ❌ **RBAC IS PARTIALLY IMPLEMENTED BUT INCOMPLETE**

The application has **subscription tier infrastructure** (FREE, PRO, ENTERPRISE) but **lacks complete role-based access control**. There is **NO admin panel functionality to manage user tiers**, and the implementation needs significant work.

---

## Current Implementation Status

### ✅ What IS Implemented

#### 1. **Subscription Tier Model** (Transaction Model)
```python
# File: backend/authentication/models.py

SUBSCRIPTION_TIER_CHOICES = [
    ('FREE', 'Free'),
    ('PRO', 'Pro'),
    ('ENTERPRISE', 'Enterprise'),
]

# In Transaction model
subscription_tier = models.CharField(
    max_length=20,
    choices=SUBSCRIPTION_TIER_CHOICES,
    blank=True
)
```

#### 2. **Payment Integration for Subscription Upgrades**
- eSewa payment gateway integration
- Transaction processing with subscription tier tracking
- Automatic subscription update after successful payment

**File:** [backend/authentication/views_esewa.py](backend/authentication/views_esewa.py#L199)

```python
# When payment is verified, subscription tier is updated
if verification_successful:
    transaction_obj.status = 'COMPLETED'
    
    # Update subscription
    subscription, created = PremiumSubscription.objects.get_or_create(
        user=request.user
    )
    subscription.tier = transaction_obj.subscription_tier
    subscription.status = 'ACTIVE'
    subscription.save()
```

#### 3. **Frontend Subscription Display**
- Users can see current plan on Transactions page
- Plan information displayed with features
- Upgrade buttons available

**File:** [frontend/SecureNotes/src/views/Transactions.vue](frontend/SecureNotes/src/views/Transactions.vue#L347)

#### 4. **Basic Permission Classes**
```python
# File: backend/notes/permissions.py

class IsOwner(permissions.BasePermission):
    """
    Object-Level Permission - IDOR Prevention
    Only users can access their own notes
    """
    def has_object_permission(self, request, view, obj):
        is_owner = obj.owner == request.user
        if not is_owner:
            logger.warning(f"Unauthorized access attempt...")
        return is_owner
```

---

## ❌ What IS NOT Implemented

### 1. **PremiumSubscription Model Missing**
The code references `PremiumSubscription` but this model is **NOT CREATED**:

```python
# File: backend/authentication/views_esewa.py (line 199)
subscription = PremiumSubscription.objects.get_or_create(user=request.user)
# ❌ THIS MODEL DOES NOT EXIST - WILL CAUSE RUNTIME ERROR
```

**Location in Code:**
```python
# File: backend/authentication/views_profile.py (line 275)
# SubscriptionViewSet commented out - PremiumSubscription model not yet created
```

### 2. **No Role-Based Permission Classes**
Missing permission classes for subscription tiers:

```python
# MISSING IMPLEMENTATIONS:
class IsFreeUser(permissions.BasePermission):
    # Check if user is on FREE tier
    
class IsProUser(permissions.BasePermission):
    # Check if user is on PRO tier
    
class IsEnterpriseUser(permissions.BasePermission):
    # Check if user is on ENTERPRISE tier
```

### 3. **No Feature Access Control Based on Tier**
The application does NOT limit features by subscription level:

- ❌ Free users can create unlimited notes (should be limited to 50)
- ❌ No upload size limits based on tier
- ❌ No API access restrictions based on tier
- ❌ No feature flags for different tiers

### 4. **NO ADMIN PANEL FOR TIER MANAGEMENT**
**Critical Missing Feature:**

```python
# File: backend/notes/admin.py
# Admin only registers Note and AuditLog
# NO admin registration for:
# - UserProfile (for tier management)
# - Transaction (for payment oversight)
# - PremiumSubscription (doesn't exist)
```

**What's Missing:**
- ❌ Admin cannot view user subscription tiers
- ❌ Admin cannot manually upgrade/downgrade users
- ❌ Admin cannot manage subscription plans
- ❌ Admin cannot override user tiers
- ❌ Admin cannot force tier changes for special cases
- ❌ No admin views for subscription analytics

### 5. **No Role-Based User Model**
The User model uses Django's default, not extended with roles:

```python
# User model uses Django's default
user = models.OneToOneField(User, on_delete=models.CASCADE)

# Should have a role field like:
# role = models.CharField(choices=[('admin', 'Admin'), ('user', 'User')], default='user')
```

### 6. **Frontend Routes Not Protected by Role**
```javascript
// File: frontend/SecureNotes/src/router/index.js

// Routes check requiresAuth but NOT subscription tier
const routes = [
  {
    path: '/billing',
    name: 'Transactions',
    meta: { requiresAuth: true }  // ✓ Checks auth
    // ✗ Does NOT check if user is PRO to access API features
  }
]
```

### 7. **No Admin Routes in Frontend**
```javascript
// NO admin routes at all:
// ❌ /admin/users (manage users)
// ❌ /admin/subscriptions (manage tiers)
// ❌ /admin/transactions (oversee payments)
// ❌ /admin/analytics (view subscription analytics)
```

---

## RBAC Architecture Needed

### What Should Be Implemented

#### Backend Structure:

1. **Role Types** (Currently only tiers, need roles)
   ```python
   ROLE_CHOICES = [
       ('admin', 'Administrator'),
       ('user', 'Regular User'),
       ('support', 'Support Staff'),
   ]
   
   TIER_CHOICES = [
       ('free', 'Free Tier'),
       ('pro', 'Professional Tier'),
       ('enterprise', 'Enterprise Tier'),
   ]
   ```

2. **Permission Classes**
   ```python
   # Permission classes needed
   class IsAdmin(permissions.BasePermission)
   class IsPro(permissions.BasePermission)
   class IsEnterpriseOrPro(permissions.BasePermission)
   ```

3. **Admin Views**
   ```python
   # Admin-only endpoints
   @api_view(['GET'])
   @permission_classes([IsAdmin])
   def get_all_users_admin(request):
       # List all users with subscription info
   
   @api_view(['POST'])
   @permission_classes([IsAdmin])
   def change_user_tier(request):
       # Admin can change user tier
   ```

4. **Feature Enforcement**
   ```python
   # Limit notes by tier
   def get_note_limit(user):
       if user.profile.subscription.tier == 'free':
           return 50
       elif user.profile.subscription.tier == 'pro':
           return 1000
       else:  # enterprise
           return 99999
   ```

#### Frontend Structure:

1. **Admin Dashboard Route**
   ```javascript
   {
     path: '/admin',
     component: AdminDashboard,
     meta: { requiresAuth: true, requiresRole: 'admin' }
   }
   ```

2. **Role-Based Navigation Guards**
   ```javascript
   router.beforeEach((to, from, next) => {
     const requiredRole = to.meta.requiresRole
     const userRole = store.user.role
     
     if (requiredRole && userRole !== requiredRole) {
       next('/unauthorized')
     }
   })
   ```

---

## Code Issues Found

### Issue 1: PremiumSubscription Model Referenced But Not Created
**File:** [backend/authentication/views_esewa.py:199](backend/authentication/views_esewa.py#L199)

```python
subscription = PremiumSubscription.objects.get_or_create(user=request.user)
# ❌ PremiumSubscription model doesn't exist - WILL FAIL AT RUNTIME
```

**Solution:** Create the model in `authentication/models.py`:
```python
class PremiumSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIER_CHOICES, default='FREE')
    status = models.CharField(max_length=20, default='INACTIVE')
    billing_cycle_start = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Issue 2: No Subscription Tier Field in UserProfile
**File:** [backend/authentication/models.py:1-100](backend/authentication/models.py#L1)

The `UserProfile` model should have subscription info, not just in Transaction:
```python
# ADD to UserProfile model:
subscription_tier = models.CharField(
    max_length=20,
    choices=SUBSCRIPTION_TIER_CHOICES,
    default='FREE'
)
```

### Issue 3: Admin Panel Not Configured
**File:** [backend/notes/admin.py](backend/notes/admin.py)

Missing admin registrations:
```python
# MISSING:
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_tier', 'two_factor_enabled']
    list_editable = ['subscription_tier']  # Admin can change tier
    search_fields = ['user__username']
```

### Issue 4: No Frontend Admin Views
**Missing Files:**
- ❌ `frontend/SecureNotes/src/views/AdminDashboard.vue`
- ❌ `frontend/SecureNotes/src/views/AdminUsers.vue`
- ❌ `frontend/SecureNotes/src/views/AdminSubscriptions.vue`

---

## Security Recommendations

### 🔴 Critical Issues

1. **PremiumSubscription Model Missing**
   - **Risk:** Application will crash when payment is verified
   - **Priority:** IMMEDIATE - Create model and migration
   - **Effort:** 30 minutes

2. **No Admin Tier Management**
   - **Risk:** Admins cannot fix incorrect subscription states
   - **Priority:** HIGH - Implement admin panel
   - **Effort:** 2-3 hours

3. **No Permission Enforcement**
   - **Risk:** Free users can access PRO features if they manually manipulate API
   - **Priority:** HIGH - Add permission classes
   - **Effort:** 1-2 hours

### 🟡 Important Issues

4. **No Feature Limits by Tier**
   - **Risk:** All users get unlimited access regardless of tier
   - **Priority:** MEDIUM - Implement feature gates
   - **Effort:** 2 hours

5. **Missing Subscription Endpoints**
   - **Risk:** Users cannot see/manage their subscription
   - **Priority:** MEDIUM - Create subscription API endpoints
   - **Effort:** 1 hour

### 🟢 Nice to Have

6. **Subscription Analytics**
   - **Risk:** No visibility into subscription metrics
   - **Priority:** LOW - Create analytics dashboard
   - **Effort:** 2-3 hours

---

## Implementation Roadmap

### Phase 1: Foundation (Required)
- [ ] Create `PremiumSubscription` model
- [ ] Run migrations
- [ ] Add subscription_tier to UserProfile
- [ ] Create tier-based permission classes

**Estimated Time:** 1 hour
**Blocking Issues:** YES - Will fix runtime crashes

### Phase 2: Admin Panel (Important)
- [ ] Register UserProfile in admin
- [ ] Register Transaction in admin  
- [ ] Register PremiumSubscription in admin
- [ ] Create admin change list filters
- [ ] Allow manual tier changes (with audit logging)

**Estimated Time:** 2 hours
**Blocking Issues:** NO - But needed for production

### Phase 3: Feature Enforcement (Important)
- [ ] Implement note limit checks
- [ ] Implement upload size checks
- [ ] Implement API access controls
- [ ] Add appropriate error messages

**Estimated Time:** 2 hours
**Blocking Issues:** NO - But allows free-to-pro upgrade monetization

### Phase 4: Frontend Admin (Nice to Have)
- [ ] Create admin dashboard
- [ ] Create user management interface
- [ ] Create subscription management interface
- [ ] Add role-based route guards

**Estimated Time:** 3-4 hours
**Blocking Issues:** NO - Can use Django admin initially

---

## Current RBAC Coverage

| Feature | Implemented | Location | Status |
|---------|------------|----------|--------|
| **Subscription Tiers** | Partially | models.py | Transaction model only, UserProfile missing |
| **Permission Classes** | Minimal | permissions.py | Only IsOwner, no tier-based permissions |
| **Admin Panel** | No | admin.py | Notes and AuditLog only |
| **Feature Limiting** | No | - | No enforcement |
| **Frontend Role Guards** | No | router/index.js | No role-based routing |
| **Payment Integration** | Partially | views_esewa.py | Works but references missing model |
| **User Tier Management** | No | - | Cannot change tiers |

---

## Test Cases for Missing RBAC

```bash
# Test 1: Create user, verify tier is FREE
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "Test123!"}'

# Should create with tier: FREE

# Test 2: Admin should be able to change tier
curl -X POST http://localhost:8000/api/admin/users/1/change-tier/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier": "pro"}'

# Currently: ❌ Endpoint doesn't exist

# Test 3: Free user should be limited to 50 notes
curl -X POST http://localhost:8000/api/notes/ ... # Create 51 notes
# Currently: ❌ All 51 created (no limit enforced)

# Test 4: Check subscription on user endpoint
curl -X GET http://localhost:8000/api/auth/user/ \
  -H "Authorization: Bearer TOKEN"

# Should return subscription tier in response
```

---

## Conclusion

**RBAC Implementation Status: 40% Complete**

The application has:
- ✅ Subscription tier infrastructure (in Transaction model)
- ✅ Payment integration for tier upgrades
- ✅ Basic object-level access control (IsOwner)

But is **missing**:
- ❌ PremiumSubscription model (causes runtime errors)
- ❌ Admin panel to manage tiers
- ❌ Role-based permission classes
- ❌ Feature enforcement by tier
- ❌ Frontend admin interface
- ❌ Subscription endpoints for users

**Recommendation:** Prioritize implementing Phase 1 and Phase 2 before going to production, as the current implementation will crash when users upgrade their subscription.

