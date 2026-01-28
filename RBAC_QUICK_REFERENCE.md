# RBAC Quick Reference

## Subscription Tiers

| Tier | Price | Max Notes | Upload Size | API Access | Features |
|------|-------|-----------|-------------|------------|----------|
| **FREE** | $0 | 10 | 2 MB | ❌ | Basic notes, Markdown |
| **PRO** | $5/mo | 100 | 50 MB | ✅ | Advanced formatting, Sharing, Tags |
| **ENTERPRISE** | $20/mo | 5000 | 500 MB | ✅ | All features, Team collab, SSO |

---

## Protecting Endpoints

### Only PRO Users
```python
from notes.permissions import IsProUser
from rest_framework.decorators import permission_classes

@permission_classes([IsProUser])
def premium_endpoint(request):
    pass
```

### Only ENTERPRISE Users
```python
from notes.permissions import IsEnterpriseUser

@permission_classes([IsEnterpriseUser])
def enterprise_only(request):
    pass
```

### Only Staff/Admin
```python
from notes.permissions import IsAdmin

@permission_classes([IsAdmin])
def admin_only(request):
    pass
```

### FREE Users Only
```python
from notes.permissions import IsFreeUser

@permission_classes([IsFreeUser])
def free_tier_endpoint(request):
    pass
```

---

## Checking Limits in Views

```python
from notes.rbac_utils import check_note_limit, check_upload_size_limit

# Before creating a note
limit = check_note_limit(request.user)
if not limit['allowed']:
    return Response({'error': limit['message']}, status=402)

# Before uploading file
if not check_upload_size_limit(request.user, 50):  # 50 MB
    return Response({'error': 'File too large'}, status=413)
```

---

## Admin Panel Changes

**URL:** `http://localhost:8000/admin/`

1. Go to **Authentication > User Profiles**
2. Click subscription_tier column to change user's tier
3. Change is **instant** - user gets new permissions immediately
4. View transaction history in **Notes > Transactions**
5. Manage subscriptions in **Notes > Premium Subscriptions**

---

## Tier Check in Code

```python
from notes.rbac_utils import get_user_tier_info

info = get_user_tier_info(user)
# {
#     'tier': 'PRO',
#     'max_notes': 100,
#     'current_notes': 42,
#     'remaining_notes': 58,
#     'max_upload_size_mb': 50,
#     'features': ['advanced_formatting', 'sharing', 'tags']
# }
```

---

## Testing Tiers

```bash
# Test in Python shell
python manage.py shell

from django.contrib.auth.models import User
from authentication.models import UserProfile, PremiumSubscription

# Change tier programmatically
user = User.objects.get(username='testuser')
profile = UserProfile.objects.get(user=user)
profile.subscription_tier = 'PRO'
profile.save()

premium = PremiumSubscription.objects.get(user=user)
premium.tier = 'PRO'
premium.status = 'ACTIVE'
premium.save()
```

---

## Common Patterns

### Feature Gating
```python
if request.user.profile.subscription_tier in ['PRO', 'ENTERPRISE']:
    # Show PRO features
    pass
else:
    # Show upgrade prompt
    pass
```

### Tier-based Responses
```python
tier = request.user.profile.subscription_tier
if tier == 'FREE':
    limit = 10
elif tier == 'PRO':
    limit = 100
else:  # ENTERPRISE
    limit = 5000
```

### Check Before Action
```python
from notes.rbac_utils import check_note_limit

def create_note(request):
    limit = check_note_limit(request.user)
    if not limit['allowed']:
        return Response({
            'error': 'Note limit reached',
            'current': limit['current_count'],
            'limit': limit['limit'],
            'message': limit['message']
        }, status=402)
    
    # Create note
    return Response(status=201)
```

---

## Default User Tier

- **New users:** `subscription_tier='FREE'`
- **After payment:** Upgraded to PRO or ENTERPRISE based on transaction
- **Admin can:** Change tier anytime via admin panel

---

## Status Values for PremiumSubscription

- `'ACTIVE'` - Subscription is active
- `'INACTIVE'` - Subscription is not active (default)
- `'CANCELLED'` - User cancelled subscription
- `'SUSPENDED'` - Admin suspended subscription

---

## Troubleshooting

**User not getting new tier:**
- Check both `UserProfile.subscription_tier` AND `PremiumSubscription.tier`
- Both must match for proper RBAC
- Check `PremiumSubscription.status` is `'ACTIVE'`

**Permission denied error:**
- Verify user tier with: `user.profile.subscription_tier`
- Check permission class is correctly imported
- Ensure `request.user` is authenticated

**Feature limits not working:**
- Call `check_note_limit()` or `check_upload_size_limit()` in view
- Return `status=402` (Payment Required) when limit exceeded
- Update limits in `rbac_utils.py > SubscriptionLimits.LIMITS`
