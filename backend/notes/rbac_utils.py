# File: backend/notes/rbac_utils.py
"""
RBAC Utility Functions - Feature gating and tier-based limits
"""

from django.conf import settings


class SubscriptionLimits:
    """
    Define feature limits for each subscription tier
    """
    LIMITS = {
        'FREE': {
            'max_notes': 50,
            'max_upload_size_mb': 5,
            'api_access': False,
            'features': ['basic_notes', 'text_only'],
        },
        'PRO': {
            'max_notes': 1000,
            'max_upload_size_mb': 500,
            'api_access': True,
            'features': ['basic_notes', 'file_uploads', 'advanced_search', 'api_access'],
        },
        'ENTERPRISE': {
            'max_notes': 999999,
            'max_upload_size_mb': 5000,
            'api_access': True,
            'features': ['basic_notes', 'file_uploads', 'advanced_search', 'api_access', 'team_management', 'custom_integrations'],
        },
    }
    
    @staticmethod
    def get_limit(tier, limit_type):
        """
        Get a specific limit for a tier
        
        Args:
            tier: 'FREE', 'PRO', or 'ENTERPRISE'
            limit_type: 'max_notes', 'max_upload_size_mb', 'api_access'
        
        Returns:
            The limit value or None if not found
        """
        return SubscriptionLimits.LIMITS.get(tier, {}).get(limit_type)
    
    @staticmethod
    def get_max_notes(tier):
        """Get maximum number of notes allowed for tier"""
        return SubscriptionLimits.get_limit(tier, 'max_notes') or 50
    
    @staticmethod
    def get_max_upload_size_mb(tier):
        """Get maximum upload size in MB for tier"""
        return SubscriptionLimits.get_limit(tier, 'max_upload_size_mb') or 5
    
    @staticmethod
    def has_api_access(tier):
        """Check if tier has API access"""
        return SubscriptionLimits.get_limit(tier, 'api_access') or False
    
    @staticmethod
    def get_features(tier):
        """Get list of available features for tier"""
        return SubscriptionLimits.get_limit(tier, 'features') or []


def check_note_limit(user):
    """
    Check if user has reached their note limit based on subscription tier
    
    Returns:
        dict: {
            'allowed': bool,
            'current_count': int,
            'limit': int,
            'message': str
        }
    """
    try:
        tier = user.profile.subscription_tier
        current_count = user.notes.count()
        limit = SubscriptionLimits.get_max_notes(tier)
        
        return {
            'allowed': current_count < limit,
            'current_count': current_count,
            'limit': limit,
            'message': f"You have {current_count}/{limit} notes"
        }
    except Exception as e:
        # If profile doesn't exist, default to FREE tier
        return {
            'allowed': True,
            'current_count': user.notes.count(),
            'limit': SubscriptionLimits.get_max_notes('FREE'),
            'message': "Error checking limit, please try again"
        }


def check_upload_size_limit(user, file_size_mb):
    """
    Check if file upload is allowed based on subscription tier
    
    Args:
        user: Django User object
        file_size_mb: File size in MB
    
    Returns:
        dict: {
            'allowed': bool,
            'file_size_mb': float,
            'limit_mb': int,
            'message': str
        }
    """
    try:
        tier = user.profile.subscription_tier
        limit_mb = SubscriptionLimits.get_max_upload_size_mb(tier)
        allowed = file_size_mb <= limit_mb
        
        return {
            'allowed': allowed,
            'file_size_mb': file_size_mb,
            'limit_mb': limit_mb,
            'message': f"File size {file_size_mb}MB exceeds limit of {limit_mb}MB for {tier} tier" if not allowed else f"File upload allowed ({file_size_mb}MB / {limit_mb}MB)"
        }
    except Exception as e:
        # Default to FREE tier limits
        limit_mb = SubscriptionLimits.get_max_upload_size_mb('FREE')
        allowed = file_size_mb <= limit_mb
        return {
            'allowed': allowed,
            'file_size_mb': file_size_mb,
            'limit_mb': limit_mb,
            'message': f"File size {file_size_mb}MB exceeds limit of {limit_mb}MB" if not allowed else f"File upload allowed ({file_size_mb}MB / {limit_mb}MB)"
        }


def check_api_access(user):
    """
    Check if user's tier has API access
    
    Returns:
        bool: True if user can access API, False otherwise
    """
    try:
        tier = user.profile.subscription_tier
        return SubscriptionLimits.has_api_access(tier)
    except:
        return False


def get_user_tier_info(user):
    """
    Get complete tier information for a user
    
    Returns:
        dict: {
            'tier': str,
            'limits': dict,
            'features': list,
            'is_active': bool
        }
    """
    try:
        tier = user.profile.subscription_tier
        
        # Check if subscription is active
        try:
            subscription = user.premium_subscription
            is_active = subscription.is_active()
        except:
            is_active = tier != 'FREE'
        
        return {
            'tier': tier,
            'limits': {
                'max_notes': SubscriptionLimits.get_max_notes(tier),
                'max_upload_size_mb': SubscriptionLimits.get_max_upload_size_mb(tier),
                'api_access': SubscriptionLimits.has_api_access(tier),
            },
            'features': SubscriptionLimits.get_features(tier),
            'is_active': is_active,
        }
    except Exception as e:
        # Default to FREE tier
        return {
            'tier': 'FREE',
            'limits': {
                'max_notes': SubscriptionLimits.get_max_notes('FREE'),
                'max_upload_size_mb': SubscriptionLimits.get_max_upload_size_mb('FREE'),
                'api_access': False,
            },
            'features': SubscriptionLimits.get_features('FREE'),
            'is_active': True,
        }
