# Making SecureNotes Secure

## E1) Password Security

### 1.1 Password Length & Complexity

**Security Concern**: Weak passwords are vulnerable to brute-force and dictionary attacks.

**Implementation**:

**Backend Validation** (`authentication/validators.py`):
```python
# File: backend/authentication/validators.py

from django.contrib.auth.password_validation import CommonPasswordValidator, MinimumLengthValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import check_password
from django.conf import settings
import re


class PasswordComplexityValidator:
    """
    Custom password validator for complexity requirements
    OWASP recommendations:
    - At least one uppercase letter [A-Z]
    - At least one lowercase letter [a-z]
    - At least one digit [0-9]
    - At least one special character [!@#$%^&*(),.?":{}|<>]
    """
    
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."),
                code='password_no_special',
            )
    
    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )
```

**Settings Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

# Password Security - Enhanced
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Increased from 8 to 12
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'authentication.validators.PasswordComplexityValidator',  # Custom validator
    },
]
```

**Frontend Validation** (`src/components/PasswordStrengthMeter.vue`):
```vue
<!-- File: frontend/SecureNotes/src/components/PasswordStrengthMeter.vue -->

<template>
  <div v-if="password" class="password-strength-meter">
    <div class="strength-bar">
      <div 
        class="strength-fill"
        :class="strengthClass"
        :style="{ width: strength + '%' }"
      ></div>
    </div>
    <div class="strength-text" :class="strengthClass">
      <i class="bi" :class="strengthIcon"></i>
      {{ strengthMessage }}
    </div>
    <div class="strength-requirements">
      <div class="requirement" :class="{ met: hasMinLength }">
        <i class="bi" :class="hasMinLength ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        At least 12 characters
      </div>
      <div class="requirement" :class="{ met: hasUppercase }">
        <i class="bi" :class="hasUppercase ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One uppercase letter
      </div>
      <div class="requirement" :class="{ met: hasLowercase }">
        <i class="bi" :class="hasLowercase ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One lowercase letter
      </div>
      <div class="requirement" :class="{ met: hasNumber }">
        <i class="bi" :class="hasNumber ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One number
      </div>
      <div class="requirement" :class="{ met: hasSpecial }">
        <i class="bi" :class="hasSpecial ? 'bi-check-circle-fill' : 'bi-x-circle'"></i>
        One special character
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { authAPI } from '../services/api'

const props = defineProps({
  password: {
    type: String,
    required: true
  }
})

const strength = ref(0)
const strengthLevel = ref('weak')
const feedback = ref([])

// Real-time password requirements validation
const hasMinLength = computed(() => props.password.length >= 12)
const hasUppercase = computed(() => /[A-Z]/.test(props.password))
const hasLowercase = computed(() => /[a-z]/.test(props.password))
const hasNumber = computed(() => /\d/.test(props.password))
const hasSpecial = computed(() => /[!@#$%^&*(),.?":{}|<>]/.test(props.password))

const strengthClass = computed(() => strengthLevel.value)

const strengthIcon = computed(() => {
  if (strengthLevel.value === 'strong') return 'bi-shield-fill-check'
  if (strengthLevel.value === 'medium') return 'bi-shield-fill-exclamation'
  return 'bi-shield-fill-x'
})

const strengthMessage = computed(() => {
  if (strengthLevel.value === 'strong') return 'Strong password'
  if (strengthLevel.value === 'medium') return 'Medium strength'
  return 'Weak password'
})

watch(() => props.password, async (newPassword) => {
  if (!newPassword) {
    strength.value = 0
    strengthLevel.value = 'weak'
    feedback.value = []
    return
  }

  try {
    const response = await authAPI.checkPasswordStrength(newPassword)
    
    // Update based on backend response
    strengthLevel.value = response.data.strength
    strength.value = response.data.score
    feedback.value = response.data.feedback || []
    
  } catch (error) {
    console.error('Error checking password strength:', error)
  }
}, { immediate: true })
</script>
```

---

### 1.2 Password Reuse Prevention

**Security Concern**: Reusing old passwords makes accounts vulnerable if previous passwords were compromised.

**Implementation**:

**PasswordHistory Model** (`authentication/models.py`):
```python
# File: backend/authentication/models.py

class PasswordHistory(models.Model):
    """
    Store password history to prevent reuse
    SECURITY: Prevents users from cycling through passwords
    - Stores hashed passwords (never plain text)
    - Tracks creation date for expiry
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
```

**Password History Check Function** (`authentication/validators.py`):
```python
# File: backend/authentication/validators.py

from django.contrib.auth.hashers import check_password

def check_password_history(user, new_password):
    """
    Check if password was used recently
    Returns True if password is acceptable (not in history)
    Returns False if password was used before
    
    SECURITY: Prevents cycling through a few passwords
    """
    from .models import PasswordHistory
    
    history_count = getattr(settings, 'PASSWORD_HISTORY_COUNT', 5)
    password_history = PasswordHistory.objects.filter(user=user).order_by('-created_at')[:history_count]
    
    # Check if new password matches any of the last 5 passwords
    for old_password in password_history:
        if check_password(new_password, old_password.password_hash):
            return False  # Password was used before
    
    return True  # Password is new and acceptable
```

**Password History in Change Password View** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='3/h', method='POST')
def change_password_view(request):
    """
    Change user password with enhanced security:
    - Password history check
    - Password strength validation
    - Rate limiting (3 attempts per hour)
    """
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response(
            {'detail': 'Both old and new passwords are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    # Step 1: Check old password is correct
    if not user.check_password(old_password):
        return Response(
            {'old_password': 'Incorrect password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Step 2: Check password history (no reuse of last 5 passwords)
    if not check_password_history(user, new_password):
        return Response(
            {'new_password': 'Cannot reuse recent passwords'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Step 3: Validate new password strength
    from django.contrib.auth.password_validation import validate_password
    try:
        validate_password(new_password, user)
    except Exception as e:
        return Response(
            {'new_password': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Step 4: Set new password
    user.set_password(new_password)
    user.save()
    
    # Step 5: Update profile password timestamp
    profile = UserProfile.objects.get(user=user)
    profile.password_changed_at = timezone.now()
    profile.force_password_change = False
    profile.save()
    
    # Step 6: Store in password history
    PasswordHistory.objects.create(
        user=user,
        password_hash=make_password(new_password)
    )
    
    # Step 7: Clean up old password history (keep only last 5)
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
```

---

### 1.3 Password Expiry Policy

**Security Concern**: Long-standing passwords increase risk of compromise over time.

**Implementation**:

**Expiry Check in User Model** (`authentication/models.py`):
```python
# File: backend/authentication/models.py

class UserProfile(models.Model):
    """
    Extended User Profile for Security & Customization
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Password Management - Track password creation date
    password_changed_at = models.DateTimeField(default=timezone.now)
    force_password_change = models.BooleanField(default=False)
    
    # ... other fields ...
    
    def is_password_expired(self):
        """
        Check if password has expired
        SECURITY: Force password change after 90 days
        """
        expiry_days = getattr(settings, 'PASSWORD_EXPIRY_DAYS', 90)
        expiry_date = self.password_changed_at + timedelta(days=expiry_days)
        return timezone.now() > expiry_date
```

**Login View Expiry Logic** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/h', method='POST')
@axes_dispatch
def login_view(request):
    """
    User Login with Enhanced Security
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(request=request, username=username, password=password)
    
    if user is None:
        # Log failed login attempt
        AuditLog.objects.create(
            user=None,
            action='FAILED_LOGIN',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details=f"Failed login attempt for username: {username}"
        )
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # CHECK PASSWORD EXPIRY - Force password change if expired
    if profile.is_password_expired():
        return Response({
            'password_expired': True,
            'message': 'Your password has expired. Please change it.',
            'user_id': user.id
        }, status=status.HTTP_403_FORBIDDEN)
    
    # ... rest of login logic ...
```

**Settings Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

# Password expiry (days)
PASSWORD_EXPIRY_DAYS = 90
```

---

### 1.4 Password Strength Meter

**Security Concern**: Users need real-time feedback to create strong passwords.

**Implementation**:

**Backend Password Strength Calculation** (`authentication/serializers.py`):
```python
# File: backend/authentication/serializers.py

class PasswordStrengthSerializer(serializers.Serializer):
    """
    Password Strength Check Serializer
    Provides real-time feedback on password strength
    """
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """
        Calculate password strength and provide feedback
        Analyzes:
        - Length (12+ = 25 points)
        - Uppercase (20 points)
        - Lowercase (20 points)
        - Numbers (20 points)
        - Special characters (15 points)
        """
        password = attrs.get('password', '')
        
        strength = 0
        feedback = []

        # Length check
        if len(password) >= 12:
            strength += 25
        elif len(password) >= 8:
            strength += 15
            feedback.append("Password should be at least 12 characters")
        else:
            feedback.append("Password is too short (minimum 8 characters)")

        # Uppercase check
        if re.search(r'[A-Z]', password):
            strength += 20
        else:
            feedback.append("Add uppercase letters")

        # Lowercase check
        if re.search(r'[a-z]', password):
            strength += 20
        else:
            feedback.append("Add lowercase letters")

        # Number check
        if re.search(r'\d', password):
            strength += 20
        else:
            feedback.append("Add numbers")

        # Special character check
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            strength += 15
        else:
            feedback.append("Add special characters")

        # Determine strength level
        if strength >= 80:
            strength_level = "strong"
            feedback = ["Password is strong!"]
        elif strength >= 60:
            strength_level = "medium"
        else:
            strength_level = "weak"

        # Return the result
        return {
            'strength': strength_level,
            'feedback': feedback,
            'score': strength
        }
```

**Backend Endpoint** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

@api_view(['POST'])
@permission_classes([AllowAny])
def check_password_strength(request):
    """
    Check password strength endpoint
    Provides real-time feedback as user types
    """
    serializer = PasswordStrengthSerializer(data=request.data)
    
    if serializer.is_valid():
        # The validated_data already contains the strength analysis
        return Response(serializer.validated_data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

---

## E2) Audit Trail & Activity Logging

### 2.1 Activity Logging System

**Security Concern**: Need to track user actions for security monitoring and forensics.

**Implementation**:

**AuditLog Model** (`notes/models.py`):
```python
# File: backend/notes/models.py

class AuditLog(models.Model):
    """
    Audit Trail Model - Security Monitoring
    - Tracks all security-relevant actions
    - Helps detect and investigate security incidents
    - IP address and user agent stored for forensics
    """
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('REGISTER', 'User Registration'),
        ('CREATE_NOTE', 'Note Created'),
        ('UPDATE_NOTE', 'Note Updated'),
        ('DELETE_NOTE', 'Note Deleted'),
        ('ACCESS_DENIED', 'Access Denied'),
        ('FAILED_LOGIN', 'Failed Login Attempt'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} - {self.action} - {self.timestamp}"
```

**IP Address Extraction Utility** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

def get_client_ip(request):
    """
    Extract client IP address from request
    SECURITY: Handles proxy headers correctly
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

**Logging in Views** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    User Registration with Audit Logging
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Log registration event
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
        }, status=status.HTTP_201_CREATED)
```

**Logging Failed Login Attempts** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/h', method='POST')
@axes_dispatch
def login_view(request):
    """
    User Login with Failed Attempt Logging
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(request=request, username=username, password=password)
    
    if user is None:
        # Log failed login attempt for security monitoring
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
    
    # Log successful login
    AuditLog.objects.create(
        user=user,
        action='LOGIN',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details=f"Successful login from IP: {get_client_ip(request)}"
    )
    
    logger.info(f"User logged in: {user.username}")
    
    # ... rest of login logic ...
```

**Security Logging Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'security.log',  # Dedicated security log file
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'security': {  # Security events logger
            'handlers': ['file'],  
            'level': 'INFO',
            'propagate': False,
        },
        'axes': {  # Brute force protection logger
            'handlers': ['file'],  
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

---

## E3) User Authentication

### 3.1 Multi-Factor Authentication (MFA/2FA)

**Security Concern**: Passwords alone are vulnerable; MFA adds an extra security layer using Time-Based One-Time Passwords (TOTP).

**Implementation**:

**TOTP Secret Generation and Storage** (`authentication/models.py`):
```python
# File: backend/authentication/models.py

class UserProfile(models.Model):
    """
    Extended User Profile for Security
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Two-Factor Authentication fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    
    # ... other fields ...
    
    def generate_totp_secret(self):
        """
        Generate a new TOTP secret for 2FA
        SECURITY: Uses pyotp library to generate random base32 encoded secret
        """
        self.two_factor_secret = pyotp.random_base32()
        self.save()
        return self.two_factor_secret
    
    def get_totp_uri(self):
        """
        Get TOTP URI for QR code generation
        SECURITY: URI includes user email and issuer name for authenticator apps
        """
        if not self.two_factor_secret:
            self.generate_totp_secret()
        
        issuer = getattr(settings, 'TWO_FACTOR_ISSUER', 'Secure Notes')
        return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
            name=self.user.email,
            issuer_name=issuer
        )
    
    def verify_totp(self, token):
        """
        Verify TOTP token
        SECURITY: Allows 30 seconds drift (valid_window=1) for clock skew
        """
        if not self.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token, valid_window=1)  # Allow 30 seconds drift
```

**MFA Setup View with QR Code** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

import pyotp
import qrcode
import io
import base64

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_two_factor(request):
    """
    Setup 2FA for user
    Returns QR code for scanning with authenticator app (Google Authenticator, Authy, Microsoft Authenticator)
    """
    serializer = TwoFactorSetupSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    enable = serializer.validated_data['enable']
    
    if enable:
        # Step 1: Generate TOTP secret
        secret = profile.generate_totp_secret()
        
        # Step 2: Generate QR code URI
        totp_uri = profile.get_totp_uri()
        
        # Step 3: Create QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Step 4: Convert to base64 for frontend display
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
```

**MFA Verification** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

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
    
    # Verify TOTP token
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
```

**MFA Check During Login** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/h', method='POST')
@axes_dispatch
def login_view(request):
    """
    User Login with MFA Support
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    two_factor_token = serializer.validated_data.get('two_factor_token', '')
    
    user = authenticate(request=request, username=username, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Check if 2FA is enabled
    if profile.two_factor_enabled:
        if not two_factor_token:
            # First response: ask for 2FA token
            return Response({
                'two_factor_required': True,
                'message': 'Please provide 2FA token'
            }, status=status.HTTP_200_OK)
        
        # Verify the TOTP token
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
    
    # MFA verified, proceed with token generation
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
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
```

---

### 3.2 Object-Level Access Control (IDOR Prevention)

**Security Concern**: Without proper access control, users can access other users' notes (Insecure Direct Object Reference - IDOR).

**Implementation**:

**Permission Classes** (`notes/permissions.py`):
```python
# File: backend/notes/permissions.py

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
        This runs on every retrieve, update, delete operation
        """
        is_owner = obj.owner == request.user
        
        if not is_owner:
            # Log unauthorized access attempt for security monitoring
            logger.warning(
                f"Unauthorized access attempt: User {request.user.username} "
                f"tried to access Note {obj.id} owned by {obj.owner.username}"
            )
        
        return is_owner
```

**Role-Based Access in Views** (`notes/views.py`):
```python
# File: backend/notes/views.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .models import Note, AuditLog
from .permissions import IsOwner

class NoteViewSet(viewsets.ModelViewSet):
    """
    Note ViewSet - Secure CRUD Operations
    
    SECURITY FEATURES:
    1. IsAuthenticated: Prevents unauthorized access
    2. IsOwner: Prevents IDOR attacks (object-level permission)
    3. get_queryset: Filters by owner (never trust client)
    4. perform_create: Auto-assigns owner (never trust user input)
    5. Audit logging: Tracks all actions
    """
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        CRITICAL SECURITY: IDOR Prevention
        - Always filter by authenticated user
        - NEVER accept user_id from request parameters
        - This ensures users only see their own notes
        """
        return Note.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        CRITICAL SECURITY: Ownership Assignment
        - Automatically assign the authenticated user as owner
        - NEVER accept owner from request data
        - Prevents privilege escalation
        """
        note = serializer.save(owner=self.request.user)
        
        # Audit log
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE_NOTE',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details=f"Created note: {note.title}"
        )
        
        logger.info(f"User {self.request.user.username} created note {note.id}")

    def perform_update(self, serializer):
        """Update with audit logging"""
        note = serializer.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE_NOTE',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details=f"Updated note: {note.title}"
        )
        
        logger.info(f"User {self.request.user.username} updated note {note.id}")

    def perform_destroy(self, instance):
        """
        SECURITY: Safe deletion
        - Delete associated files
        - Audit trail
        """
        note_id = instance.id
        note_title = instance.title
        
        # Delete file if exists
        if instance.attachment:
            try:
                instance.attachment.delete(save=False)
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
        
        instance.delete()
        
        AuditLog.objects.create(
            user=self.request.user,
            action='DELETE_NOTE',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details=f"Deleted note: {note_title}"
        )
        
        logger.info(f"User {self.request.user.username} deleted note {note_id}")

    def retrieve(self, request, *args, **kwargs):
        """
        SECURITY: Additional ownership check
        - Double-check ownership even though queryset is filtered
        - Return 403 instead of 404 for clearer security
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Note.DoesNotExist:
            # Log unauthorized access attempt
            AuditLog.objects.create(
                user=request.user,
                action='ACCESS_DENIED',
                ip_address=self.get_client_ip(),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details=f"Attempted to access note {kwargs.get('pk')}"
            )
            return Response(
                {'detail': 'Access denied or note not found.'},
                status=status.HTTP_403_FORBIDDEN
            )

    def get_client_ip(self):
        """Extract client IP for audit logging"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
```

---

## E4) Session Management

### 4.1 Secure Cookie Configuration

**Security Concern**: Insecure cookies can be intercepted or accessed by XSS attacks.

**Implementation** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

# SESSION SECURITY - ENHANCED
SESSION_COOKIE_HTTPONLY = True  # Prevent XSS access to session cookie
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection - allow safe HTTP requests
SESSION_COOKIE_AGE = 1800  # 30 minutes (reduced from 24 hours)
SESSION_SAVE_EVERY_REQUEST = True  # Refresh session on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Clear session on browser close

# CSRF PROTECTION
CSRF_COOKIE_HTTPONLY = False  # Frontend needs to read for requests
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']

# SECURITY HEADERS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'  # Clickjacking protection

# Production settings (enable when deploying)
SECURE_SSL_REDIRECT = False  # Set True in production
SECURE_HSTS_SECONDS = 31536000  # 1 year (production only)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

### 4.2 JWT Token Implementation

**Security Concern**: Stateless JWT tokens need proper lifetime management and signing.

**Implementation**:

**Token Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Short-lived access token
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),  # Longer-lived refresh token
    'ROTATE_REFRESH_TOKENS': True,  # Rotate refresh token on use
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_COOKIE': 'access_token',  # HttpOnly cookie name
    'AUTH_COOKIE_DOMAIN': None,
    'AUTH_COOKIE_SECURE': False,  # Set True in production
    'AUTH_COOKIE_HTTP_ONLY': True,  # XSS Protection
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Lax',  # CSRF Protection
}
```

**Token Generation in Login** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    User Login - Generate JWT Tokens
    """
    # ... authentication logic ...
    
    user = authenticate(request=request, username=username, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    return Response({
        'message': 'Login successful',
        'access_token': access_token,  # 1 hour lifetime
        'refresh_token': str(refresh),  # 1 day lifetime
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'two_factor_enabled': profile.two_factor_enabled
    })
```

**Token Verification** (`authentication/authentication.py`):
```python
# File: backend/authentication/authentication.py

"""
Custom Authentication Classes
Allows graceful handling of invalid tokens on public endpoints
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
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
```

**REST Framework Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.authentication.OptionalJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
```

---

## E5) Data Encryption

### 5.1 Password Hashing

**Security Concern**: Passwords must never be stored in plain text.

**Implementation**:

**Django Password Hasher Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

# Django uses PBKDF2 by default with 260,000 iterations
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
# PBKDF2 = Password-Based Key Derivation Function 2
# Uses SHA256, 260,000 iterations makes brute-force attacks slow
```

**Password Hashing in Registration** (`authentication/serializers.py`):
```python
# File: backend/authentication/serializers.py

class RegisterSerializer(serializers.ModelSerializer):
    """
    Registration Serializer - Password Hashing
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def create(self, validated_data):
        """
        Create user with hashed password
        SECURITY: Django's create_user() automatically hashes the password
        """
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']  # Automatically hashed
        )
        return user
```

**Password Verification in Login** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

from django.contrib.auth import authenticate

@api_view(['POST'])
def login_view(request):
    """
    User Login - Password Verification
    """
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    # Django's authenticate() function:
    # 1. Retrieves user from database
    # 2. Hashes provided password using PBKDF2
    # 3. Compares hash with stored hash
    # 4. Returns user if match, None otherwise
    user = authenticate(request=request, username=username, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # User authenticated - password was correct
    # ... generate JWT tokens ...
```

---

### 5.2 File Upload Security

**Security Concern**: File uploads can be exploited for malware, path traversal, or DoS attacks.

**Implementation**:

**Secure File Path Generation** (`notes/models.py`):
```python
# File: backend/notes/models.py

import uuid
import os

def note_file_path(instance, filename):
    """
    SECURITY: Path Traversal Prevention
    - Generate safe file paths using UUIDs
    - Prevent directory traversal attacks
    - Store files by user ID to enforce isolation
    """
    ext = os.path.splitext(filename)[1]
    # Use UUID instead of original filename
    new_filename = f"{uuid.uuid4()}{ext}"
    # Store under user directory
    return f"user_{instance.owner.id}/{new_filename}"


class Note(models.Model):
    """
    Note Model - File Upload Security
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    attachment = models.FileField(
        upload_to=note_file_path,  # Uses secure path function
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
            )
        ],
        help_text="Optional file attachment with security validation"
    )
```

**File Upload Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

# FILE UPLOAD SETTINGS
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' / 'uploads'  # Outside web root
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
ALLOWED_UPLOAD_EXTENSIONS = ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif']
```

---

## E6) Extra Security Features

### 6.1 Brute-Force Attack Prevention

**Security Concern**: Automated attacks can guess passwords through repeated login attempts.

**Implementation**:

**Brute Force Protection Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

INSTALLED_APPS = [
    # ...
    'axes',  # Brute force protection
    # ...
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # MUST BE FIRST - Brute force protection
    'django.contrib.auth.backends.ModelBackend',  # Default Django authentication
]

# BRUTE FORCE PROTECTION (django-axes)
AXES_FAILURE_LIMIT = 5  # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 0.1  # Lock for ~6 minutes (timedelta(minutes=6))
AXES_LOCKOUT_BY_COMBINATION_USER_AND_IP = True  # Lock per user+IP combination
AXES_RESET_ON_SUCCESS = True  # Reset counter on successful login
AXES_ENABLE_ACCESS_FAILURE_LOG = True  # Log failed attempts
AXES_VERBOSE = True

CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

**Login Rate Limiting** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

from django_ratelimit.decorators import ratelimit
from axes.decorators import axes_dispatch

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/h', method='POST')  # 10 attempts per hour per IP
@axes_dispatch  # Brute force protection
def login_view(request):
    """
    User Login with Rate Limiting and Brute Force Protection
    - Max 10 login attempts per hour per IP address
    - django-axes: Max 5 failed attempts, then 6 minute lockout
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # ... authentication logic ...
```

**Account Lockout Check** (`authentication/models.py`):
```python
# File: backend/authentication/models.py

class UserProfile(models.Model):
    """
    Account Lockout Management
    """
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    def is_account_locked(self):
        """
        Check if account is currently locked
        SECURITY: Prevents brute-force attacks
        """
        if self.account_locked_until:
            if timezone.now() < self.account_locked_until:
                return True  # Account is locked
            else:
                # Lock period expired, reset
                self.account_locked_until = None
                self.failed_login_attempts = 0
                self.save()
        return False
```

**Lockout Check in Login** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

@api_view(['POST'])
def login_view(request):
    """
    User Login - Lockout Check
    """
    # ... authentication ...
    
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
    
    # ... rest of login ...
```

---

### 6.2 CSRF Protection

**Security Concern**: Cross-Site Request Forgery (CSRF) attacks trick users into making unwanted requests.

**Implementation**:

**CSRF Middleware Configuration** (`secure_notes/settings.py`):
```python
# File: backend/secure_notes/settings.py

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF Protection - ENABLED
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CSRF_COOKIE_HTTPONLY = False  # Frontend needs to read for requests
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']
```

**Frontend CSRF Token Handling** (`src/services/api.js`):
```javascript
// File: frontend/SecureNotes/src/services/api.js

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
})

let csrfToken = null

function getCsrfToken() {
  """
  Extract CSRF token from cookies
  SECURITY: CSRF token is required for state-changing requests
  """
  if (csrfToken) return csrfToken
  
  const name = 'csrftoken'
  const cookies = document.cookie.split(';')
  
  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split('=')
    if (key === name) {
      csrfToken = decodeURIComponent(value)
      return csrfToken
    }
  }
  
  return null
}

// Add CSRF token to request headers
api.interceptors.request.use(
  (config) => {
    // Add CSRF token for state-changing requests (POST, PUT, PATCH, DELETE)
    if (['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
      const token = getCsrfToken()
      if (token) {
        config.headers['X-CSRFToken'] = token
      }
    }
    
    // Add JWT token for authentication
    const accessToken = localStorage.getItem('access_token')
    if (accessToken) {
      config.headers['Authorization'] = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)
```

---

### 6.3 Input Sanitization & XSS Prevention

**Security Concern**: User input can contain malicious code that executes in the browser (XSS attacks).

**Implementation**:

**Backend Serializer Validation** (`authentication/serializers.py`):
```python
# File: backend/authentication/serializers.py

class RegisterSerializer(serializers.ModelSerializer):
    """
    Registration Serializer - Input Validation
    DRF automatically sanitizes input through serializer validation
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        SECURITY: Email validation and normalization
        - Ensures valid email format
        - Prevents injection attacks
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_username(self, value):
        """
        SECURITY: Username validation
        - Check length
        - Check uniqueness
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        return value
```

**Frontend XSS Prevention** (`src/components/*.vue`):
```vue
<!-- XSS Prevention Example -->

<!-- ✅ SAFE: Template syntax auto-escapes HTML -->
<div class="note-content">
  {{ note.content }}
</div>

<!-- ✅ SAFE: v-text directive escapes HTML -->
<div v-text="note.content"></div>

<!-- ❌ DANGEROUS: Use v-html only with trusted content -->
<!-- <div v-html="note.content"></div> -->

<!-- ✅ SAFE: Input validation -->
<input 
  v-model="searchTerm"
  type="text"
  placeholder="Search notes..."
/>

<!-- ✅ SAFE: Binding to safe attributes -->
<a :href="`/notes/${note.id}`">View Note</a>
```

---

### 6.4 SQL Injection Prevention

**Security Concern**: Improperly constructed database queries can allow attackers to execute arbitrary SQL.

**Implementation**:

**Django ORM Prevents SQL Injection** (`notes/views.py`):
```python
# File: backend/notes/views.py

class NoteViewSet(viewsets.ModelViewSet):
    """
    Django ORM (Object-Relational Mapping) prevents SQL injection
    by using parameterized queries
    """
    
    def get_queryset(self):
        """
        ✅ SAFE: Django ORM parameterizes queries
        This is equivalent to: SELECT * FROM notes WHERE owner_id = %s
        """
        return Note.objects.filter(owner=self.request.user)
    
    # SAFE: Filtering with ORM
    # Note.objects.filter(title__icontains=search_term)
    # Note.objects.filter(created_at__gte=start_date)
    # Note.objects.filter(owner__username='john')
```

**Bad Practice (Never Do This)** - Example of what NOT to do:
```python
# ❌ DANGEROUS: Raw string concatenation
# cursor.execute(f"SELECT * FROM notes WHERE title = '{user_input}'")
# This allows SQL injection: user_input = "' OR '1'='1"

# ✅ SAFE: Use parameterized queries with ORM
# Note.objects.filter(title=user_input)
```

---

### 6.5 Payment Security (HMAC-SHA256)

**Security Concern**: Payment transactions must be protected from tampering and ensure authenticity.

**Implementation**:

**Payment Signature Generation** (`notes/esewa.py`):
```python
# File: backend/notes/esewa.py

import hmac
import hashlib
import base64
from uuid import uuid4
from datetime import datetime

def generate_esewa_form_data(order_data):
    """
    Generate eSewa payment form data with HMAC-SHA256 signature
    SECURITY: HMAC ensures transaction data cannot be tampered with
    """
    total_amount = order_data.get('total_amount')
    transaction_uuid = order_data.get('transaction_uuid')
    product_code = order_data.get('product_code', 'EPAYTEST')
    success_url = order_data.get('success_url')
    failure_url = order_data.get('failure_url')
    
    # Secret key (production: store in environment variable)
    secret_key = '8gBm/:&EnhH.1/q'  # Test Key
    
    # Format amount to 2 decimal places
    formatted_amount = f"{float(total_amount):.2f}"
    
    # Step 1: Create signature string with specific field order
    signature_string = f"total_amount={formatted_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    
    # Step 2: Generate HMAC-SHA256
    signature = base64.b64encode(
        hmac.new(
            secret_key.encode(),  # Key
            signature_string.encode(),  # Message
            hashlib.sha256  # Algorithm
        ).digest()
    ).decode()
    
    return {
        'amount': formatted_amount,
        'tax_amount': '0',
        'product_service_charge': '0',
        'product_delivery_charge': '0',
        'total_amount': formatted_amount,
        'transaction_uuid': transaction_uuid,
        'product_code': product_code,
        'success_url': success_url,
        'failure_url': failure_url,
        'signed_field_names': 'total_amount,transaction_uuid,product_code',
        'signature': signature
    }
```

**Payment Verification** (`notes/esewa.py`):
```python
# File: backend/notes/esewa.py

def verify_esewa_payment(data):
    """
    Verify eSewa Response Signature
    SECURITY: Ensures payment response came from eSewa and wasn't tampered
    """
    secret_key = '8gBm/:&EnhH.1/q'
    
    try:
        # Step 1: Get the list of fields eSewa signed
        signed_field_names = data.get('signed_field_names', '')
        
        # Step 2: Build the signature string in the same order eSewa did
        fields = signed_field_names.split(',')
        signature_string_parts = [f"{field}={data.get(field)}" for field in fields]
        signature_string = ','.join(signature_string_parts)
        
        # Step 3: Create expected signature using our secret key
        expected_signature = base64.b64encode(
            hmac.new(
                secret_key.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        # Step 4: Compare signatures (timing-attack resistant comparison would be better)
        is_valid = data.get('signature') == expected_signature
        
        return is_valid
    
    except Exception as error:
        print(f"Signature Verification Error: {error}")
        return False


def generate_transaction_uuid():
    """
    Generate unique transaction UUID for eSewa
    SECURITY: Ensures each transaction is unique
    """
    timestamp = int(datetime.now().timestamp() * 1000)
    random_part = str(uuid4())[:8]
    return f"LUX-{timestamp}-{random_part}"
```

---

### 6.6 Registration Rate Limiting

**Security Concern**: Rapid account creation can be used for spam, abuse, or brute-force attacks.

**Implementation** (`authentication/views.py`):
```python
# File: backend/authentication/views.py

from django_ratelimit.decorators import ratelimit

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/h', method='POST')  # 5 registrations per hour per IP
def register_view(request):
    """
    User Registration with Rate Limiting
    - Max 5 registrations per hour per IP address
    - Prevents spam and abuse
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Log registration
        AuditLog.objects.create(
            user=user,
            action='REGISTER',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details=f"New user registered: {user.username}"
        )
        
        return Response({
            'message': 'User registered successfully',
            'username': user.username,
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

---

## E7) Role-Based Access Control (RBAC)

### 7.1 Subscription Tier System

**Security Concern**: Different users have different feature access levels. Need to enforce tier-based feature access and limits.

**Implementation**:

**Database Models** (`authentication/models.py`):
```python
# File: backend/authentication/models.py (lines 154-227)

class PremiumSubscription(models.Model):
    """
    Premium Subscription Model - Track subscription status
    SECURITY FEATURES:
    - RBAC: Stores user's subscription tier and status
    - Billing: Tracks billing cycle dates
    - Audit: Tracks when subscription changes occur
    - Feature gating: Used to enforce tier-based limits
    """
    TIER_CHOICES = [
        ('FREE', 'Free'),
        ('PRO', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('CANCELLED', 'Cancelled'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='premium_subscription')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='FREE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INACTIVE')
    billing_cycle_start = models.DateTimeField(null=True, blank=True)
    billing_cycle_end = models.DateTimeField(null=True, blank=True)
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'ACTIVE'
    
    def is_expired(self):
        """Check if subscription billing cycle has expired"""
        if not self.billing_cycle_end:
            return False
        return timezone.now() > self.billing_cycle_end
```

**UserProfile Enhancement** (`authentication/models.py` lines 51-62):
```python
# File: backend/authentication/models.py

# Subscription & RBAC
subscription_tier = models.CharField(
    max_length=20,
    choices=[
        ('FREE', 'Free'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ],
    default='FREE',
    help_text="User's current subscription tier"
)
```

---

### 7.2 Permission Classes

**Security Concern**: Need to restrict API endpoints based on user subscription tier.

**Implementation** (`notes/permissions.py`):
```python
# File: backend/notes/permissions.py (lines 48-100)

from rest_framework.permissions import BasePermission

class IsProUser(BasePermission):
    """Only PRO and ENTERPRISE tier users can access"""
    def has_permission(self, request, view):
        return request.user.profile.subscription_tier in ['PRO', 'ENTERPRISE']

class IsEnterpriseUser(BasePermission):
    """Only ENTERPRISE tier users can access"""
    def has_permission(self, request, view):
        return request.user.profile.subscription_tier == 'ENTERPRISE'

class IsFreeUser(BasePermission):
    """Only FREE tier users can access"""
    def has_permission(self, request, view):
        return request.user.profile.subscription_tier == 'FREE'

class IsProOrEnterprise(BasePermission):
    """Requires PRO or ENTERPRISE (excludes FREE)"""
    def has_permission(self, request, view):
        return request.user.profile.subscription_tier in ['PRO', 'ENTERPRISE']

class IsAdmin(BasePermission):
    """Only staff/admin users can access"""
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser
```

**Usage Example**:
```python
from rest_framework.decorators import api_view, permission_classes
from notes.permissions import IsProUser

@api_view(['POST'])
@permission_classes([IsProUser])
def create_advanced_note(request):
    """Only PRO and ENTERPRISE users can create advanced notes"""
    # Implementation...
```

---

### 7.3 Feature Limiting System

**Security Concern**: Different tiers have different feature limits (note count, upload size, API access).

**Implementation** (`notes/rbac_utils.py`):
```python
# File: backend/notes/rbac_utils.py (170+ lines)

class SubscriptionLimits:
    """Define feature limits for each subscription tier"""
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
            'features': ['basic_notes', 'file_uploads', 'advanced_search', 'api_access', 
                        'team_management', 'custom_integrations'],
        },
    }

def check_note_limit(user):
    """Check if user can create more notes based on tier"""
    tier = user.profile.subscription_tier
    max_notes = SubscriptionLimits.get_max_notes(tier)
    current_count = user.notes.count()
    
    return {
        'allowed': current_count < max_notes,
        'current_count': current_count,
        'limit': max_notes,
        'message': f"Note limit: {current_count}/{max_notes}"
    }

def check_upload_size_limit(user, file_size_mb):
    """Check if file size is within tier limit"""
    tier = user.profile.subscription_tier
    limit_mb = SubscriptionLimits.get_max_upload_size_mb(tier)
    allowed = file_size_mb <= limit_mb
    
    return {
        'allowed': allowed,
        'file_size_mb': file_size_mb,
        'limit_mb': limit_mb,
        'message': f"Upload limit: {limit_mb}MB for {tier} tier"
    }

def get_user_tier_info(user):
    """Get complete tier information for a user"""
    tier = user.profile.subscription_tier
    return {
        'tier': tier,
        'limits': {
            'max_notes': SubscriptionLimits.get_max_notes(tier),
            'max_upload_size_mb': SubscriptionLimits.get_max_upload_size_mb(tier),
            'api_access': SubscriptionLimits.has_api_access(tier),
        },
        'features': SubscriptionLimits.get_features(tier),
    }
```

**Usage in Views**:
```python
from notes.rbac_utils import check_note_limit

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_note(request):
    """Create note with tier-based limit checking"""
    limit = check_note_limit(request.user)
    if not limit['allowed']:
        return Response(limit, status=status.HTTP_402_PAYMENT_REQUIRED)
    
    # Create note...
    return Response(note_data, status=status.HTTP_201_CREATED)
```

---

### 7.4 Admin Panel Management

**Security Concern**: Admins need to manage user subscription tiers securely.

**Implementation** (`notes/admin.py`):
```python
# File: backend/notes/admin.py (lines 132-250)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_tier', 'two_factor_enabled', 'note_count', 'created_at']
    list_editable = ['subscription_tier']  # ✅ Admins can edit tier directly
    list_filter = ['subscription_tier', 'two_factor_enabled']
    search_fields = ['user__username', 'user__email']

@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'status', 'is_active_display', 'created_at']
    list_filter = ['tier', 'status']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'payment_method', 'subscription_tier', 'created_at']
    list_filter = ['status', 'payment_method', 'subscription_tier']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
```

**Admin Actions**:
1. Navigate to Django Admin: `/admin/authentication/userprofile/`
2. Find user and click `subscription_tier` column
3. Change tier and save
4. User immediately gets new permissions and limits

---

### 7.5 Payment Integration

**Security Concern**: When users make payments, both RBAC models must be updated consistently.

**Implementation** (`authentication/views_esewa.py`):
```python
# File: backend/authentication/views_esewa.py

def verify_esewa_payment(pidx, source):
    """
    Verify eSewa payment and update RBAC models
    SECURITY: Syncs both UserProfile and PremiumSubscription tiers
    """
    # ... payment verification ...
    
    # Update both RBAC models atomically
    profile = UserProfile.objects.get(user=user)
    profile.subscription_tier = new_tier
    profile.save()
    
    premium = PremiumSubscription.objects.get(user=user)
    premium.tier = new_tier
    premium.status = 'ACTIVE'
    premium.billing_cycle_start = timezone.now()
    premium.billing_cycle_end = timezone.now() + timedelta(days=365)
    premium.save()
    
    # ... create transaction record ...
```

---

### 7.6 Tier Limits Summary

| Feature | FREE | PRO | ENTERPRISE |
|---------|------|-----|------------|
| **Max Notes** | 50 | 1,000 | 999,999 |
| **Upload Size** | 5 MB | 500 MB | 5,000 MB |
| **API Access** | ❌ No | ✅ Yes | ✅ Yes |
| **Advanced Search** | ❌ No | ✅ Yes | ✅ Yes |
| **File Uploads** | ❌ No | ✅ Yes | ✅ Yes |
| **Team Management** | ❌ No | ❌ No | ✅ Yes |
| **Custom Integrations** | ❌ No | ❌ No | ✅ Yes |

---

## Security Summary

SecureNotes implements comprehensive security features across multiple layers:

| Feature | Implementation | Benefit |
|---------|------------------|---------|
| **Password Security** | 12+ char, complexity validation, history tracking, 90-day expiry | Prevents weak passwords & reuse |
| **MFA/2FA** | TOTP (Time-Based One-Time Passwords) with QR code | Adds second factor of authentication |
| **Role-Based Access Control** | 3-tier system (FREE/PRO/ENTERPRISE), 5 permission classes, feature limits | Enforces tier-based feature access |
| **Subscription Tiers** | PremiumSubscription model with status tracking, configurable limits | Different access levels per tier |
| **Feature Limiting** | rbac_utils.py with per-tier note/upload/API limits | Prevents limit circumvention |
| **Admin Tier Management** | Django admin with editable tier field, audit trail via transactions | Secure admin control |
| **Brute Force Protection** | django-axes: 5 attempts → 6 min lockout | Prevents password guessing |
| **Rate Limiting** | Per-IP rate limits on auth endpoints | Prevents automated attacks |
| **CSRF Protection** | Token-based CSRF protection | Prevents cross-site requests |
| **Session Security** | HttpOnly cookies, 30-min timeout | Prevents XSS & session hijacking |
| **JWT Tokens** | 1-hour access token, 1-day refresh token | Stateless authentication |
| **IDOR Prevention** | Object-level permissions, owner filtering | Prevents unauthorized access |
| **Audit Logging** | All security events logged with IP & user agent | Enables forensics & monitoring |
| **File Upload Security** | UUID naming, extension validation, size limits | Prevents path traversal & uploads |
| **Payment Security** | HMAC-SHA256 signatures, RBAC model sync | Prevents payment tampering |
| **Input Validation** | DRF serializers, Django ORM | Prevents SQL injection & XSS |
| **Security Headers** | X-Frame-Options, HSTS, CSP | Prevents clickjacking & downgrade attacks |
| **Password Hashing** | PBKDF2 with 260,000 iterations | Resistant to brute-force attacks |

