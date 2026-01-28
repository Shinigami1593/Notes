# RBAC Implementation Examples

Complete, copy-paste-ready code examples for integrating RBAC into your application.

---

## 1. Protect Note Creation with Tier Limits

### Current Code (Without RBAC)
```python
# notes/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Note
from .serializers import NoteSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_note(request):
    serializer = NoteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
```

### With RBAC Tier Limits
```python
# notes/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Note
from .serializers import NoteSerializer
from .rbac_utils import check_note_limit  # ✅ ADD THIS

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_note(request):
    # ✅ ADD: Check tier-based note limit
    limit_check = check_note_limit(request.user)
    if not limit_check['allowed']:
        return Response({
            'error': 'Note limit reached',
            'current_notes': limit_check['current_count'],
            'max_notes': limit_check['limit'],
            'message': limit_check['message'],
            'upgrade_url': '/upgrade'
        }, status=status.HTTP_402_PAYMENT_REQUIRED)
    
    serializer = NoteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
```

---

## 2. Protect File Upload with Size Limits

### Current Code
```python
# notes/views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_attachment(request):
    file = request.FILES['file']
    
    # Save file
    attachment = Attachment.objects.create(
        note_id=request.data['note_id'],
        file=file,
        uploaded_by=request.user
    )
    return Response(AttachmentSerializer(attachment).data, status=201)
```

### With RBAC Size Limits
```python
# notes/views.py
from .rbac_utils import check_upload_size_limit  # ✅ ADD THIS

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_attachment(request):
    file = request.FILES['file']
    
    # ✅ ADD: Check file size limit based on tier
    file_size_mb = file.size / (1024 * 1024)
    if not check_upload_size_limit(request.user, file_size_mb):
        tier = request.user.profile.subscription_tier
        limit = {'FREE': 2, 'PRO': 50, 'ENTERPRISE': 500}[tier]
        return Response({
            'error': 'File too large for your plan',
            'file_size_mb': round(file_size_mb, 2),
            'max_size_mb': limit,
            'tier': tier,
            'upgrade_url': '/upgrade'
        }, status=status.HTTP_413_PAYLOAD_TOO_LARGE)
    
    # Save file
    attachment = Attachment.objects.create(
        note_id=request.data['note_id'],
        file=file,
        uploaded_by=request.user
    )
    return Response(AttachmentSerializer(attachment).data, status=201)
```

---

## 3. API Access Limited to PRO Users

### Using Permission Class
```python
# notes/views.py
from .permissions import IsProUser

@api_view(['GET'])
@permission_classes([IsProUser])  # ✅ Only PRO and ENTERPRISE
def get_notes_via_api(request):
    """
    REST API access only for PRO and ENTERPRISE users.
    FREE users see 403 Forbidden.
    """
    notes = Note.objects.filter(user=request.user)
    serializer = NoteSerializer(notes, many=True)
    return Response(serializer.data)
```

### Response to FREE User
```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

## 4. Enterprise-Only Feature

```python
# notes/views.py
from .permissions import IsEnterpriseUser

@api_view(['POST'])
@permission_classes([IsEnterpriseUser])  # ✅ Only ENTERPRISE
def enable_sso(request):
    """Single Sign-On setup only for Enterprise tier"""
    profile = request.user.profile
    profile.sso_enabled = True
    profile.save()
    return Response({'sso_enabled': True})
```

---

## 5. Admin-Only Endpoint

```python
# notes/views.py
from .permissions import IsAdmin

@api_view(['GET'])
@permission_classes([IsAdmin])  # ✅ Only staff/admin
def get_subscription_analytics(request):
    """System administrators only"""
    from django.contrib.auth.models import User
    from authentication.models import PremiumSubscription
    
    stats = {
        'total_users': User.objects.count(),
        'pro_users': PremiumSubscription.objects.filter(tier='PRO').count(),
        'enterprise_users': PremiumSubscription.objects.filter(tier='ENTERPRISE').count(),
        'revenue': PremiumSubscription.objects.filter(
            status='ACTIVE'
        ).count() * 5,  # Rough estimate
    }
    return Response(stats)
```

---

## 6. Tier-based Response Data

### Different Data for Different Tiers
```python
# notes/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """Return dashboard data filtered by tier"""
    user = request.user
    tier = user.profile.subscription_tier
    
    # Basic info for all tiers
    data = {
        'tier': tier,
        'note_count': user.notes.count(),
    }
    
    # Add PRO-specific analytics
    if tier in ['PRO', 'ENTERPRISE']:
        from django.db.models import Count
        data['note_stats'] = {
            'total': user.notes.count(),
            'by_category': dict(
                user.notes.values('category').annotate(count=Count('id'))
            ),
            'last_7_days': user.notes.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
    
    # Add ENTERPRISE-specific data
    if tier == 'ENTERPRISE':
        data['team_members'] = user.profile.team_members.count()
        data['api_calls_this_month'] = user.api_logs.filter(
            created_at__month=timezone.now().month
        ).count()
    
    return Response(data)
```

---

## 7. Combining Multiple Permission Checks

```python
# notes/views.py
from rest_framework.permissions import IsAuthenticated
from .permissions import IsProUser, IsAdmin

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProUser | IsAdmin])  # ✅ PRO users OR admins
def share_note_with_team(request):
    """Share notes with team - PRO+ or admin only"""
    # This runs only if user is:
    # 1. Authenticated AND
    # 2. Either PRO/ENTERPRISE tier OR is staff
    pass
```

---

## 8. Custom Permission for Shared Features

```python
# notes/permissions.py
from rest_framework.permissions import BasePermission

class CanManageTeam(BasePermission):
    """Only ENTERPRISE users or staff can manage teams"""
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        return request.user.profile.subscription_tier == 'ENTERPRISE'

# Usage:
@api_view(['POST'])
@permission_classes([CanManageTeam])
def add_team_member(request):
    pass
```

---

## 9. Upgrade Prompt Response

```python
# notes/views.py
from .rbac_utils import get_user_tier_info

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_feature_access(request, feature_name):
    """
    Check if user has access to a feature.
    Return upgrade info if needed.
    """
    tier = request.user.profile.subscription_tier
    required_tier = {
        'advanced_formatting': 'PRO',
        'sharing': 'PRO',
        'sso': 'ENTERPRISE',
        'team_collaboration': 'ENTERPRISE',
    }.get(feature_name, 'FREE')
    
    tier_order = {'FREE': 0, 'PRO': 1, 'ENTERPRISE': 2}
    has_access = tier_order[tier] >= tier_order[required_tier]
    
    if has_access:
        return Response({
            'feature': feature_name,
            'allowed': True,
            'current_tier': tier
        })
    else:
        return Response({
            'feature': feature_name,
            'allowed': False,
            'current_tier': tier,
            'required_tier': required_tier,
            'upgrade_url': '/upgrade?plan=' + required_tier.lower(),
            'message': f'This feature requires {required_tier} tier'
        }, status=status.HTTP_402_PAYMENT_REQUIRED)
```

---

## 10. Class-Based View Example

```python
# notes/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsProUser
from .rbac_utils import check_note_limit

class NoteListCreateView(APIView):
    """
    List notes and create new notes with tier-based limits
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user's notes"""
        notes = Note.objects.filter(user=request.user)
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create new note (with tier limits)"""
        # ✅ Check tier limit
        limit_check = check_note_limit(request.user)
        if not limit_check['allowed']:
            return Response(
                limit_check,
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
```

---

## 11. Monitoring Feature Usage

```python
# notes/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usage_report(request):
    """Show user their current usage vs tier limits"""
    from .rbac_utils import get_user_tier_info
    
    tier_info = get_user_tier_info(request.user)
    
    return Response({
        'tier': tier_info['tier'],
        'notes': {
            'used': tier_info['current_notes'],
            'limit': tier_info['max_notes'],
            'percentage': (tier_info['current_notes'] / tier_info['max_notes']) * 100
        },
        'storage': {
            'limit_mb': tier_info['max_upload_size_mb'],
            'message': f"Your {tier_info['tier']} plan allows {tier_info['max_upload_size_mb']}MB uploads"
        },
        'features': tier_info['features'],
        'upgrade_url': '/upgrade' if tier_info['tier'] == 'FREE' else None
    })
```

---

## 12. Test Cases

```python
# notes/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from authentication.models import UserProfile, PremiumSubscription

class RBACTestCase(TestCase):
    def setUp(self):
        # Create users
        self.free_user = User.objects.create_user(
            username='free_user',
            password='pass123'
        )
        UserProfile.objects.create(
            user=self.free_user,
            subscription_tier='FREE'
        )
        PremiumSubscription.objects.create(
            user=self.free_user,
            tier='FREE'
        )
        
        self.pro_user = User.objects.create_user(
            username='pro_user',
            password='pass123'
        )
        UserProfile.objects.create(
            user=self.pro_user,
            subscription_tier='PRO'
        )
        PremiumSubscription.objects.create(
            user=self.pro_user,
            tier='PRO',
            status='ACTIVE'
        )
        
        self.client = APIClient()
    
    def test_free_user_cannot_access_pro_endpoint(self):
        """FREE users should get 403 for PRO endpoints"""
        self.client.force_authenticate(user=self.free_user)
        response = self.client.get('/api/pro-feature/')
        self.assertEqual(response.status_code, 403)
    
    def test_pro_user_can_access_pro_endpoint(self):
        """PRO users should get 200 for PRO endpoints"""
        self.client.force_authenticate(user=self.pro_user)
        response = self.client.get('/api/pro-feature/')
        self.assertEqual(response.status_code, 200)
    
    def test_note_limit_enforced(self):
        """FREE users limited to 10 notes"""
        # Create 10 notes for FREE user
        for i in range(10):
            Note.objects.create(
                user=self.free_user,
                title=f"Note {i}"
            )
        
        # 11th note should fail
        self.client.force_authenticate(user=self.free_user)
        response = self.client.post('/api/notes/', {
            'title': 'Note 11',
            'content': 'Should fail'
        })
        self.assertEqual(response.status_code, 402)  # Payment Required
```

---

## Quick Checklist

- [ ] Import permission classes or rbac_utils in your views
- [ ] Add `@permission_classes([IsProUser])` decorator if needed
- [ ] Call `check_note_limit()` before creating notes
- [ ] Call `check_upload_size_limit()` before uploading files
- [ ] Return `status=402` when limits are exceeded
- [ ] Test with users of all three tiers
- [ ] Update API documentation with tier requirements
- [ ] Add frontend "upgrade required" prompts
- [ ] Monitor tier-based feature usage in analytics

---

## Common Mistakes to Avoid

❌ **Don't:** Hardcode tier checks
```python
# BAD
if request.user.username == 'admin':
    return Response(data)
```

✅ **Do:** Use permission classes
```python
# GOOD
@permission_classes([IsAdmin])
def admin_view(request):
    return Response(data)
```

---

❌ **Don't:** Forget to sync both tier fields
```python
# BAD - only updates one
user.profile.subscription_tier = 'PRO'
user.profile.save()
```

✅ **Do:** Update both models
```python
# GOOD - syncs both
user.profile.subscription_tier = 'PRO'
user.profile.save()
user.premium_subscription.tier = 'PRO'
user.premium_subscription.save()
```

---

❌ **Don't:** Return generic 403 errors
```python
# BAD
return Response({'error': 'Forbidden'}, status=403)
```

✅ **Do:** Return helpful 402 with upgrade info
```python
# GOOD
return Response({
    'error': 'Feature not available',
    'current_tier': 'FREE',
    'required_tier': 'PRO',
    'upgrade_url': '/upgrade'
}, status=402)
```
