from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from axes.decorators import axes_dispatch
import pyotp
import qrcode
import io
import base64
import logging

from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    PasswordStrengthSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer
)
from .models import UserProfile, PasswordHistory
from .validators import check_password_history
from notes.models import AuditLog

logger = logging.getLogger('security')


def get_client_ip(request):
    """Extract client IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/h', method='POST')
def register_view(request):
    """
    User Registration with Security Features:
    - Password strength validation
    - Password complexity requirements
    - Rate limiting
    """
    # Clear any authentication errors for public endpoint
    request.user = None
    request.auth = None
    
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create user profile
        from .models import UserProfile
        UserProfile.objects.create(user=user)
        
        # Audit log
        AuditLog.objects.create(
            user=user,
            action='REGISTER',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details=f"New user registered: {user.username}"
        )
        
        logger.info(f"New user registered: {user.username}")
        
        return Response({
            'message': 'User registered successfully',
            'username': user.username,
            'two_factor_required': False
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/h', method='POST')
@axes_dispatch
def login_view(request):
    """
    User Login with Enhanced Security
    """
    # Clear any authentication errors for public endpoint
    request.user = None
    request.auth = None
    
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    two_factor_token = serializer.validated_data.get('two_factor_token', '')
    
    user = authenticate(request=request, username=username, password=password)
    
    if user is None:
        AuditLog.objects.create(
            user=None,
            action='FAILED_LOGIN',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details=f"Failed login attempt for username: {username}"
        )
        logger.warning(f"Failed login attempt for: {username}")
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if profile.is_account_locked():
        AuditLog.objects.create(
            user=user,
            action='ACCESS_DENIED',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details="Account is locked"
        )
        return Response(
            {'detail': 'Account is locked. Please try again later.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if profile.two_factor_enabled:
        if not two_factor_token:
            return Response({
                'two_factor_required': True,
                'message': 'Please provide 2FA token'
            }, status=status.HTTP_200_OK)
        
        if not profile.verify_totp(two_factor_token):
            AuditLog.objects.create(
                user=user,
                action='FAILED_LOGIN',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details="Invalid 2FA token"
            )
            return Response(
                {'detail': 'Invalid 2FA token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    if profile.is_password_expired():
        return Response({
            'password_expired': True,
            'message': 'Your password has expired. Please change it.',
            'user_id': user.id
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    # Update profile
    profile.last_login_ip = get_client_ip(request)
    profile.last_login_user_agent = request.META.get('HTTP_USER_AGENT', '')
    profile.failed_login_attempts = 0
    profile.last_failed_login = None
    profile.save()
    
    # Audit log
    AuditLog.objects.create(
        user=user,
        action='LOGIN',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details=f"Successful login"
    )
    
    logger.info(f"User logged in: {user.username}")
    
    # Return tokens in response body
    return Response({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'two_factor_enabled': profile.two_factor_enabled
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User Logout"""
    username = request.user.username
    
    AuditLog.objects.create(
        user=request.user,
        action='LOGOUT',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details="User logged out"
    )
    
    logger.info(f"User logged out: {username}")
    
    response = Response({'message': 'Logout successful'})
    response.delete_cookie('access_token')
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Get current authenticated user"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'two_factor_enabled': profile.two_factor_enabled,
        'password_expired': profile.is_password_expired()
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def check_password_strength(request):
    """
    Check password strength
    SECURITY: No rate limiting on this endpoint to allow real-time feedback
    """
    # Clear any authentication errors for public endpoint
    request.user = None
    request.auth = None
    
    serializer = PasswordStrengthSerializer(data=request.data)
    
    if serializer.is_valid():
        # The validated_data already contains the strength analysis
        return Response(serializer.validated_data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_two_factor(request):
    """
    Setup 2FA for user
    Returns QR code for scanning with authenticator app
    """
    serializer = TwoFactorSetupSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    enable = serializer.validated_data['enable']
    
    if enable:
        # Generate TOTP secret
        secret = profile.generate_totp_secret()
        
        # Generate QR code
        totp_uri = profile.get_totp_uri()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'qr_code': f'data:image/png;base64,{img_str}',
            'secret': secret,
            'message': 'Scan QR code with your authenticator app'
        })
    else:
        # Disable 2FA
        profile.two_factor_enabled = False
        profile.two_factor_secret = None
        profile.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE_NOTE',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details="2FA disabled"
        )
        
        return Response({'message': '2FA disabled successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_two_factor(request):
    """
    Verify and enable 2FA
    User must provide valid token to confirm setup
    """
    serializer = TwoFactorVerifySerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.verify_totp(token):
        profile.two_factor_enabled = True
        profile.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE_NOTE',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details="2FA enabled successfully"
        )
        
        return Response({'message': '2FA enabled successfully'})
    else:
        return Response(
            {'detail': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='3/h', method='POST')
def change_password_view(request):
    """
    Change user password with enhanced security:
    - Password history check
    - Password strength validation
    - Rate limiting
    """
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response(
            {'detail': 'Both old and new passwords are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    # Check old password
    if not user.check_password(old_password):
        return Response(
            {'old_password': 'Incorrect password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check password history
    if not check_password_history(user, new_password):
        return Response(
            {'new_password': 'Cannot reuse recent passwords'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new password
    from django.contrib.auth.password_validation import validate_password
    try:
        validate_password(new_password, user)
    except Exception as e:
        return Response(
            {'new_password': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    # Update profile
    profile = UserProfile.objects.get(user=user)
    profile.password_changed_at = timezone.now()
    profile.force_password_change = False
    profile.save()
    
    # Store in password history
    PasswordHistory.objects.create(
        user=user,
        password_hash=make_password(new_password)
    )
    
    # Clean up old password history
    history_count = getattr(settings, 'PASSWORD_HISTORY_COUNT', 5)
    old_passwords = PasswordHistory.objects.filter(user=user).order_by('-created_at')[history_count:]
    for old_pass in old_passwords:
        old_pass.delete()
    
    AuditLog.objects.create(
        user=user,
        action='UPDATE_NOTE',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details="Password changed"
    )
    
    logger.info(f"Password changed for user: {user.username}")
    
    return Response({'message': 'Password changed successfully'})
