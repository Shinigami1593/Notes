"""
Custom Exception Handler for DRF
Allows unauthenticated access to public endpoints even with invalid tokens
"""
from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that treats invalid tokens as unauthenticated
    rather than returning 401 Unauthorized
    """
    # Handle JWT token errors
    if hasattr(exc, 'detail'):
        error_detail = str(exc.detail)
        
        # If token is invalid but endpoint allows AllowAny, don't fail the request
        # Let the view handle it with AllowAny permission
        if 'token' in error_detail.lower() or 'invalid' in error_detail.lower():
            # Check if view allows unauthenticated access
            view = context.get('view')
            if view and hasattr(view, 'permission_classes'):
                from rest_framework.permissions import AllowAny
                if AllowAny in view.permission_classes:
                    # This endpoint allows anonymous access, ignore token errors
                    return None
    
    # Call the default exception handler
    response = exception_handler(exc, context)
    return response
