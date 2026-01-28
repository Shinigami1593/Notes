from rest_framework import permissions
import logging

logger = logging.getLogger('security')


class IsOwner(permissions.BasePermission):
    """
    SECURITY: Object-Level Permission
    - Prevents IDOR (Insecure Direct Object Reference)
    - Ensures users can only access their own notes
    - Logs unauthorized access attempts
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user owns the object
        """
        is_owner = obj.owner == request.user
        
        if not is_owner:
            # Log unauthorized access attempt for security monitoring
            logger.warning(
                f"Unauthorized access attempt: User {request.user.username} "
                f"tried to access Note {obj.id} owned by {obj.owner.username}"
            )
        
        return is_owner


class IsFreeUser(permissions.BasePermission):
    """
    RBAC: Check if user has FREE tier subscription
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.profile.subscription_tier == 'FREE'


class IsProUser(permissions.BasePermission):
    """
    RBAC: Check if user has PRO tier or higher
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.profile.subscription_tier in ['PRO', 'ENTERPRISE']


class IsEnterpriseUser(permissions.BasePermission):
    """
    RBAC: Check if user has ENTERPRISE tier
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.profile.subscription_tier == 'ENTERPRISE'


class IsProOrEnterprise(permissions.BasePermission):
    """
    RBAC: Check if user has PRO or ENTERPRISE tier (excludes FREE)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.profile.subscription_tier in ['PRO', 'ENTERPRISE']


class IsAdmin(permissions.BasePermission):
    """
    RBAC: Check if user is staff/admin
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.is_superuser