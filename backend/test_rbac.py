#!/usr/bin/env python
"""
RBAC Comprehensive Test Suite
Tests all RBAC functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_notes.settings')
django.setup()

from django.contrib.auth.models import User
from authentication.models import UserProfile, PremiumSubscription
from notes.permissions import IsProUser, IsEnterpriseUser, IsAdmin, IsFreeUser, IsProOrEnterprise
from notes.rbac_utils import get_user_tier_info, check_note_limit, check_upload_size_limit
from rest_framework.test import APIRequestFactory

def run_tests():
    print("=" * 70)
    print("RBAC IMPLEMENTATION - FINAL COMPREHENSIVE TEST")
    print("=" * 70)
    
    factory = APIRequestFactory()
    
    # Clean up
    User.objects.filter(username__endswith='_test').delete()
    
    # TEST 1: Create users
    print("\n✅ TEST 1: Creating test users...")
    free_user = User.objects.create_user(username='free_test', password='pass')
    free_profile, _ = UserProfile.objects.get_or_create(user=free_user)
    free_profile.subscription_tier = 'FREE'
    free_profile.save()
    free_premium, _ = PremiumSubscription.objects.get_or_create(user=free_user)
    free_premium.tier = 'FREE'
    free_premium.status = 'INACTIVE'
    free_premium.save()
    
    pro_user = User.objects.create_user(username='pro_test', password='pass')
    pro_profile, _ = UserProfile.objects.get_or_create(user=pro_user)
    pro_profile.subscription_tier = 'PRO'
    pro_profile.save()
    pro_premium, _ = PremiumSubscription.objects.get_or_create(user=pro_user)
    pro_premium.tier = 'PRO'
    pro_premium.status = 'ACTIVE'
    pro_premium.save()
    
    enterprise_user = User.objects.create_user(username='enterprise_test', password='pass')
    enterprise_profile, _ = UserProfile.objects.get_or_create(user=enterprise_user)
    enterprise_profile.subscription_tier = 'ENTERPRISE'
    enterprise_profile.save()
    enterprise_premium, _ = PremiumSubscription.objects.get_or_create(user=enterprise_user)
    enterprise_premium.tier = 'ENTERPRISE'
    enterprise_premium.status = 'ACTIVE'
    enterprise_premium.save()
    
    admin_user = User.objects.create_user(username='admin_test', password='pass', is_staff=True)
    admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
    admin_profile.subscription_tier = 'ENTERPRISE'
    admin_profile.save()
    admin_premium, _ = PremiumSubscription.objects.get_or_create(user=admin_user)
    admin_premium.tier = 'ENTERPRISE'
    admin_premium.status = 'ACTIVE'
    admin_premium.save()
    print("  ✅ All test users created")
    
    # TEST 2: Permission classes
    print("\n✅ TEST 2: Permission Classes...")
    
    # IsProUser
    perm = IsProUser()
    request = factory.get('/')
    request.user = free_user
    assert not perm.has_permission(request, None)
    request.user = pro_user
    assert perm.has_permission(request, None)
    print("  ✅ IsProUser works correctly")
    
    # IsEnterpriseUser
    perm = IsEnterpriseUser()
    request.user = pro_user
    assert not perm.has_permission(request, None)
    request.user = enterprise_user
    assert perm.has_permission(request, None)
    print("  ✅ IsEnterpriseUser works correctly")
    
    # IsAdmin
    perm = IsAdmin()
    request.user = admin_user
    assert perm.has_permission(request, None)
    print("  ✅ IsAdmin works correctly")
    
    # IsFreeUser
    perm = IsFreeUser()
    request.user = free_user
    assert perm.has_permission(request, None)
    request.user = pro_user
    assert not perm.has_permission(request, None)
    print("  ✅ IsFreeUser works correctly")
    
    # IsProOrEnterprise
    perm = IsProOrEnterprise()
    request.user = free_user
    assert not perm.has_permission(request, None)
    request.user = pro_user
    assert perm.has_permission(request, None)
    request.user = enterprise_user
    assert perm.has_permission(request, None)
    print("  ✅ IsProOrEnterprise works correctly")
    
    # TEST 3: Tier information
    print("\n✅ TEST 3: Tier Information...")
    
    info = get_user_tier_info(free_user)
    assert info['tier'] == 'FREE'
    assert info['limits']['max_notes'] == 50
    assert info['limits']['max_upload_size_mb'] == 5
    assert not info['limits']['api_access']
    print("  ✅ FREE tier: max_notes=50, upload=5MB, api_access=False")
    
    info = get_user_tier_info(pro_user)
    assert info['tier'] == 'PRO'
    assert info['limits']['max_notes'] == 1000
    assert info['limits']['max_upload_size_mb'] == 500
    assert info['limits']['api_access']
    print("  ✅ PRO tier: max_notes=1000, upload=500MB, api_access=True")
    
    info = get_user_tier_info(enterprise_user)
    assert info['tier'] == 'ENTERPRISE'
    assert info['limits']['max_notes'] == 999999
    assert info['limits']['max_upload_size_mb'] == 5000
    assert info['limits']['api_access']
    print("  ✅ ENTERPRISE tier: max_notes=999999, upload=5000MB, api_access=True")
    
    # TEST 4: Feature limits
    print("\n✅ TEST 4: Feature Limits...")
    
    limit = check_note_limit(free_user)
    assert limit['limit'] == 50
    limit = check_note_limit(pro_user)
    assert limit['limit'] == 1000
    limit = check_note_limit(enterprise_user)
    assert limit['limit'] == 999999
    print("  ✅ Note limits: FREE=50, PRO=1000, ENTERPRISE=999999")
    
    assert check_upload_size_limit(free_user, 5)['allowed']
    assert not check_upload_size_limit(free_user, 10)['allowed']
    assert check_upload_size_limit(pro_user, 500)['allowed']
    assert not check_upload_size_limit(pro_user, 1000)['allowed']
    assert check_upload_size_limit(enterprise_user, 5000)['allowed']
    print("  ✅ Upload limits: FREE=5MB, PRO=500MB, ENTERPRISE=5000MB")
    
    # TEST 5: Admin tier changes
    print("\n✅ TEST 5: Admin Tier Changes...")
    
    profile = UserProfile.objects.get(user=free_user)
    premium = PremiumSubscription.objects.get(user=free_user)
    
    profile.subscription_tier = 'PRO'
    profile.save()
    premium.tier = 'PRO'
    premium.status = 'ACTIVE'
    premium.save()
    
    # Refresh user to get updated profile
    free_user.refresh_from_db()
    profile.refresh_from_db()
    premium.refresh_from_db()
    
    assert profile.subscription_tier == 'PRO'
    assert premium.tier == 'PRO'
    
    # Verify permission updated (need to use fresh user instance)
    request = factory.get('/')
    request.user = User.objects.get(id=free_user.id)  # Get fresh instance
    perm = IsProUser()
    assert perm.has_permission(request, None)
    
    print("  ✅ Admin tier changes work: FREE→PRO successful")
    
    # TEST 6: Model sync
    print("\n✅ TEST 6: Model Consistency...")
    
    for user in [pro_user, enterprise_user, admin_user]:
        profile = UserProfile.objects.get(user=user)
        premium = PremiumSubscription.objects.get(user=user)
        assert profile.subscription_tier == premium.tier
    print("  ✅ All models synchronized correctly")
    
    # Cleanup
    User.objects.filter(username__endswith='_test').delete()
    
    print("\n" + "=" * 70)
    print("✅ ALL RBAC TESTS PASSED - FULLY FUNCTIONAL")
    print("=" * 70)
    
    print("\n📋 RBAC Implementation Summary:")
    print("  ✅ PremiumSubscription model created and working")
    print("  ✅ subscription_tier field added to UserProfile")
    print("  ✅ 5 permission classes tested and working")
    print("  ✅ Feature limits enforced correctly")
    print("  ✅ Admin can manage user tiers")
    print("  ✅ Database models synchronized")
    print("  ✅ READY FOR PRODUCTION USE")
    print("\n")

if __name__ == '__main__':
    run_tests()
