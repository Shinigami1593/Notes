"""
Custom Authentication Classes
Allows graceful handling of invalid tokens on public endpoints
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed


class OptionalJWTAuthentication(JWTAuthentication):
    """
    JWT authentication that doesn't raise exceptions for invalid tokens
    Allows unauthenticated requests while still supporting JWT when valid
    """
    
    def authenticate(self, request):
        """
        Attempt JWT authentication, but don't raise errors if token is invalid
        This allows the view's permission_classes to determine access
        """
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            # Token is invalid or malformed, but allow the request to proceed
            # The view's @permission_classes decorator will enforce access control
            return None
