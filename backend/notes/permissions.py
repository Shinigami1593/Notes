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