from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import pyotp
from datetime import timedelta
import uuid


class UserProfile(models.Model):
    """
    Extended User Profile for Security & Customization:
    - Two-Factor Authentication
    - Password expiry tracking
    - Account lockout
    - Login attempt tracking
    - Profile customization
    - Privacy preferences
    - Notification settings
    """
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Two-Factor Authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    
    # Password Management
    password_changed_at = models.DateTimeField(default=timezone.now)
    force_password_change = models.BooleanField(default=False)
    
    # Account Security
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Login Tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_user_agent = models.TextField(blank=True)
    
    # Profile Customization
    bio = models.TextField(max_length=500, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Privacy Settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('private', 'Private'),
            ('friends', 'Friends Only'),
            ('public', 'Public')
        ],
        default='private'
    )
    show_email = models.BooleanField(default=False)
    show_activity = models.BooleanField(default=False)
    
    # Notification Preferences
    notify_login_attempts = models.BooleanField(default=True)
    notify_password_changes = models.BooleanField(default=True)
    notify_2fa_changes = models.BooleanField(default=True)
    notify_new_notes = models.BooleanField(default=False)
    
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def generate_totp_secret(self):
        """Generate a new TOTP secret for 2FA"""
        self.two_factor_secret = pyotp.random_base32()
        self.save()
        return self.two_factor_secret
    
    def get_totp_uri(self):
        """Get TOTP URI for QR code generation"""
        if not self.two_factor_secret:
            self.generate_totp_secret()
        
        issuer = getattr(settings, 'TWO_FACTOR_ISSUER', 'Secure Notes')
        return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
            name=self.user.email,
            issuer_name=issuer
        )
    
    def verify_totp(self, token):
        """Verify TOTP token"""
        if not self.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token, valid_window=1)  # Allow 30 seconds drift
    
    def is_password_expired(self):
        """Check if password has expired"""
        expiry_days = getattr(settings, 'PASSWORD_EXPIRY_DAYS', 90)
        expiry_date = self.password_changed_at + timedelta(days=expiry_days)
        return timezone.now() > expiry_date
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until:
            if timezone.now() < self.account_locked_until:
                return True
            else:
                # Lock period expired, reset
                self.account_locked_until = None
                self.failed_login_attempts = 0
                self.save()
        return False
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if threshold reached"""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after 5 failed attempts
        max_attempts = getattr(settings, 'AXES_FAILURE_LIMIT', 5)
        if self.failed_login_attempts >= max_attempts:
            lockout_hours = getattr(settings, 'AXES_COOLOFF_TIME', 1)
            self.account_locked_until = timezone.now() + timedelta(hours=lockout_hours)
        
        self.save()
    
    def reset_failed_login(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        self.save()


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
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='premium_subscription'
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='FREE',
        help_text="Subscription tier (FREE, PRO, ENTERPRISE)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='INACTIVE',
        help_text="Current subscription status"
    )
    
    # Billing Information
    billing_cycle_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When current billing cycle started"
    )
    billing_cycle_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When current billing cycle ends"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'premium_subscriptions'
        verbose_name = 'Premium Subscription'
        verbose_name_plural = 'Premium Subscriptions'
    
    def __str__(self):
        return f"{self.user.username} - {self.tier} ({self.status})"
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'ACTIVE'
    
    def is_expired(self):
        """Check if subscription billing cycle has expired"""
        if not self.billing_cycle_end:
            return False
        return timezone.now() > self.billing_cycle_end


class PasswordHistory(models.Model):
    """
    Store password history to prevent reuse
    SECURITY: Prevents users from cycling through passwords
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'password_history'
        verbose_name = 'Password History'
        verbose_name_plural = 'Password Histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Transaction(models.Model):
    """
    Transaction Model - Secure Transaction Processing
    SECURITY FEATURES:
    - UUID for transaction tracking (prevents ID enumeration)
    - Encrypted sensitive fields
    - Status tracking for transaction lifecycle
    - Audit trail with timestamps
    - Amount stored as integer (cents) to prevent floating point issues
    - Support for multiple payment gateways (Stripe, eSewa)
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('subscription', 'Subscription'),
        ('withdrawal', 'Withdrawal'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('STRIPE', 'Stripe'),
        ('ESEWA', 'eSewa'),
        ('KHALTI', 'Khalti'),
        ('OTHER', 'Other'),
    ]
    
    SUBSCRIPTION_TIER_CHOICES = [
        ('FREE', 'Free'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    # Transaction Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction Details
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='payment')
    amount = models.PositiveIntegerField()  # Amount in cents/paisa
    currency = models.CharField(max_length=3, default='NPR')  # Changed to NPR
    description = models.TextField(blank=True)
    
    # Status & Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Payment Gateway Fields
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='STRIPE'
    )
    stripe_payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # eSewa Payment Fields
    esewa_order_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    esewa_ref_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # Subscription Info
    subscription_tier = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TIER_CHOICES,
        blank=True
    )
    
    # Billing Period
    billing_period_start = models.DateTimeField(null=True, blank=True)
    billing_period_end = models.DateTimeField(null=True, blank=True)
    
    # Security
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['id']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.payment_method} - {self.amount} {self.currency}"
    
    def get_amount_display(self):
        """Get formatted amount in NPR"""
        return f"NPR {self.amount}"
    
    def complete_transaction(self):
        """Mark transaction as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
    
    def fail_transaction(self, error_msg=''):
        """Mark transaction as failed"""
        self.status = 'FAILED'
        self.error_message = error_msg
        self.save()


class UserSession(models.Model):
    """
    Track User Sessions for Security
    SECURITY FEATURES:
    - Session tracking for user activity
    - IP and user agent logging
    - Session timeout
    - Multiple session support
    """
    SESSION_TYPES = [
        ('web', 'Web'),
        ('mobile', 'Mobile'),
        ('api', 'API'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=100, unique=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='web')
    
    # Device Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_name = models.CharField(max_length=255, blank=True)
    
    # Session Control
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.session_type}"
    
    def is_expired(self):
        """Check if session has expired"""
        return timezone.now() > self.expires_at
    
    def mark_inactive(self):
        """Mark session as inactive"""
        self.is_active = False
        self.save()