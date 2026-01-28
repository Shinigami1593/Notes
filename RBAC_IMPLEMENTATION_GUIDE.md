# RBAC Implementation Guide

## Overview

Role-Based Access Control (RBAC) has been implemented in SecureNotes with three subscription tiers: FREE, PRO, and ENTERPRISE. This guide explains the implementation and how to use it.

---

## 1. Models

### PremiumSubscription Model
```python
# File: backend/authentication/models.py

class PremiumSubscription(models.Model):
    """
    Tracks user's subscription tier and status
    """
    TIER_CHOICES = [
        ('FREE', 'Free'),
        ('PRO', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    user = models.OneToOneField(User, related_name='premium_subscription')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='FREE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INACTIVE')
    billing_cycle_start = models.DateTimeField(null=True, blank=True)
    billing_cycle_end = models.DateTimeField(null=True, blank=True)
```

### UserProfile Extension
```python
# Added subscription_tier field to UserProfile for quick access
subscription_tier = models.CharField(
    max_length=20,
    choices=[('FREE', 'Free'), ('PRO', 'Pro'), ('ENTERPRISE', 'Enterprise')],
    default='FREE'
)
```

---

## 2. Permission Classes

### Available Permission Classes
Located in `backend/notes/permissions.py`:

```python
# Check specific tiers
IsProUser()           # PRO tier only
IsEnterpriseUser()    # ENTERPRISE tier only
IsProOrEnterprise()   # PRO or ENTERPRISE (not FREE)

# Admin access
IsAdmin()             # Staff/superuser only
```

### Usage in Views
```python
from rest_framework.decorators import permission_classes
from notes.permissions import IsProUser

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProUser])
def create_api_endpoint(request):
    """Only PRO users can access this"""
    pass
```

---

## 3. Subscription Limits (RBAC Utils)

### Feature Limits by Tier
File: `backend/notes/rbac_utils.py`

| Feature | FREE | PRO | ENTERPRISE |
|---------|------|-----|------------|
| Max Notes | 50 | 1,000 | 999,999 |
| Max Upload (MB) | 5 | 500 | 5,000 |
| API Access | ❌ | ✅ | ✅ |
| Team Management | ❌ | ❌ | ✅ |

### Using RBAC Utils
```python
from notes.rbac_utils import SubscriptionLimits, check_note_limit, check_api_access

# Get limit for a tier
limit = SubscriptionLimits.get_max_notes('PRO')  # Returns 1000

# Check if user can add more notes
result = check_note_limit(user)
if not result['allowed']:
    return Response({'error': result['message']}, status=402)

# Check API access
if not check_api_access(user):
    return Response({'error': 'API access requires PRO tier'}, status=403)

# Get complete user tier info
info = get_user_tier_info(user)
# Returns: {tier, limits, features, is_active}
```

---

## 4. Admin Panel

### User Profile Admin
Admins can now:
- View all user subscription tiers
- **Change tier directly from list view** (`list_editable`)
- Monitor 2FA status and security settings

**Access:** Django Admin > User Profiles

### PremiumSubscription Admin
Admins can:
- View all active subscriptions
- **Change subscription tier and status** from list view
- Monitor billing cycles

**Access:** Django Admin > Premium Subscriptions

### Transaction Admin
Admins can:
- View all payment transactions
- Filter by status, payment method, tier
- Audit payment history

**Access:** Django Admin > Transactions

---

## 5. Payment Integration

### Automatic Tier Updates
When user completes eSewa payment:

```python
# File: backend/authentication/views_esewa.py

# Payment verified
subscription.tier = transaction_obj.subscription_tier
subscription.status = 'ACTIVE'
subscription.save()

# UserProfile also updated (for RBAC checks)
profile.subscription_tier = transaction_obj.subscription_tier
profile.save()
```

---

## 6. Enforcing Feature Limits

### Example: Enforce Note Limit
```python
# In note creation view
from notes.rbac_utils import check_note_limit

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_note(request):
    limit_check = check_note_limit(request.user)
    
    if not limit_check['allowed']:
        return Response({
            'error': limit_check['message'],
            'current': limit_check['current_count'],
            'limit': limit_check['limit']
        }, status=402)  # 402 Payment Required
    
    # Create note
    note = Note.objects.create(owner=request.user, ...)
    return Response({'message': 'Note created'})
```

### Example: Enforce Upload Limit
```python
from notes.rbac_utils import check_upload_size_limit

file_size_mb = request.FILES['file'].size / (1024 * 1024)
size_check = check_upload_size_limit(request.user, file_size_mb)

if not size_check['allowed']:
    return Response({
        'error': size_check['message'],
        'limit_mb': size_check['limit_mb']
    }, status=402)
```

---

## 7. Testing RBAC

### Test 1: Create User with Default Tier
```bash
# Register user - should default to FREE
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "Test123!", "password2": "Test123!"}'

# Check user profile in admin - should see tier: FREE
```

### Test 2: Admin Change Tier
```bash
# In Django Admin:
1. Go to User Profiles
2. Select a user
3. Change subscription_tier to 'PRO'
4. Click Save

# User now has PRO features (1,000 notes limit, 500MB upload)
```

### Test 3: Check Tier Info Endpoint
```bash
# Get user's tier info
curl -X GET http://localhost:8000/api/auth/user/ \
  -H "Authorization: Bearer TOKEN"

# Should return: subscription_tier: "FREE" or "PRO" or "ENTERPRISE"
```

### Test 4: Enforce Note Limit
```bash
# Create 50 notes as FREE user (should succeed)
# Create 51st note (should fail with 402 Payment Required)
```

---

## 8. Database Schema

### New Tables
- `premium_subscriptions` - Tracks subscription status and tier
- Updated `user_profiles` - Now includes subscription_tier

### Relationships
```
User (Django Auth)
├── UserProfile (1:1)
│   └── subscription_tier (RBAC check)
├── PremiumSubscription (1:1)
│   ├── tier (Subscription level)
│   └── status (ACTIVE/INACTIVE)
└── Transaction (1:many)
    └── subscription_tier (What was purchased)
```

---

## 9. Migration

### Running Migrations
```bash
python manage.py makemigrations authentication
python manage.py migrate
```

### What Was Added
- `UserProfile.subscription_tier` field
- `PremiumSubscription` model

### Backward Compatibility
- Existing users default to FREE tier
- No breaking changes to existing fields
- Safe to run on existing databases

---

## 10. API Endpoints (Future)

### Planned Endpoints
```python
# Get current subscription
GET /api/subscriptions/current/

# Get available plans
GET /api/subscriptions/plans/

# Upgrade plan
POST /api/subscriptions/upgrade/

# Get tier info
GET /api/subscriptions/tier-info/
```

---

## 11. Best Practices

### ✅ DO:
- Always check `user.profile.subscription_tier` for quick access
- Use permission classes for simple tier checks
- Use RBAC utils for complex feature limiting
- Log tier changes in audit logs
- Sync UserProfile and PremiumSubscription on updates

### ❌ DON'T:
- Trust client-side tier claims
- Allow bypassing tier limits with API parameters
- Skip audit logging for admin tier changes
- Forget to update both UserProfile and PremiumSubscription

---

## 12. Security Considerations

### Authorization Checks
- All tier-based endpoints require `@permission_classes([IsAuthenticated])`
- Tier is verified server-side, never trusted from client
- Logs record all admin tier changes

### Rate Limiting
- FREE tier may get stricter rate limits (optional)
- PRO/ENTERPRISE get higher rate limits
- Enforce via custom middleware if needed

### Audit Trail
- All tier changes logged in AuditLog
- PremiumSubscription tracks status changes
- Admin changes tracked for compliance

---

## 13. Configuration

### Environment Variables
```bash
# Optional: In production, configure these
SUBSCRIPTION_EXPIRY_DAYS=30    # Auto-expire subscriptions
TRIAL_PERIOD_DAYS=7            # Free trial length
```

### Settings
All configuration is in `backend/notes/rbac_utils.py`
Edit the `SubscriptionLimits.LIMITS` dict to customize limits per tier

---

## 14. Troubleshooting

### Issue: User tier not updating after payment
**Solution:** Check that both UserProfile and PremiumSubscription are updated in payment verification

### Issue: Admin can't change tier
**Solution:** Ensure staff/superuser permissions are set, check list_editable in admin

### Issue: Feature limit not enforced
**Solution:** Call `check_note_limit()` before allowing operation

### Issue: Migration failed
**Solution:** 
```bash
python manage.py migrate authentication --fake-initial
python manage.py migrate authentication
```

---

## Summary

RBAC is now fully implemented with:
- ✅ Subscription tier model
- ✅ Permission classes for tier checking
- ✅ Admin panel for tier management
- ✅ Utility functions for feature limiting
- ✅ Database migrations
- ✅ Payment integration
- ✅ Audit logging

The implementation is production-ready and backward compatible.
