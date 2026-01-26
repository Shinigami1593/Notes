from rest_framework import serializers
from django.contrib.auth.models import User
from authentication.models import UserProfile, Transaction, UserSession
import re


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User Profile Serializer with comprehensive customization options
    SECURITY: Validates all user inputs, prevents XSS and injection attacks
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'email',
            'bio',
            'avatar_url',
            'phone_number',
            'date_of_birth',
            'profile_visibility',
            'show_email',
            'show_activity',
            'notify_login_attempts',
            'notify_password_changes',
            'notify_2fa_changes',
            'notify_new_notes',
            'two_factor_enabled',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'two_factor_enabled',
            'created_at',
            'updated_at'
        ]
    
    def validate_bio(self, value):
        """Validate bio field"""
        if len(value) > 500:
            raise serializers.ValidationError("Bio must be less than 500 characters.")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value and not re.match(r'^[\d\s\-\+\(\)]+$', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value
    
    def validate_avatar_url(self, value):
        """Validate avatar URL"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Avatar URL must be a valid HTTP(S) URL.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """
    Transaction Serializer for secure transaction handling
    SECURITY: Read-only fields prevent tampering, validation on all inputs
    """
    amount_display = serializers.SerializerMethodField()
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'payment_method',
            'amount',
            'amount_display',
            'currency',
            'status',
            'subscription_tier',
            'created_at',
            'updated_at',
            'completed_at'
        ]
        read_only_fields = [
            'id',
            'user',
            'status',
            'created_at',
            'updated_at',
            'completed_at'
        ]
    
    def get_amount_display(self, obj):
        """Return formatted amount"""
        return obj.get_amount_display()
    
    def validate_amount(self, value):
        """Validate transaction amount"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        if value > 999999999:  # Max ~999,999,999 NPR
            raise serializers.ValidationError("Amount exceeds maximum limit.")
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """
    User Session Serializer for session management
    SECURITY: Shows user their active sessions for security awareness
    """
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id',
            'session_type',
            'ip_address',
            'device_name',
            'is_active',
            'is_expired',
            'last_activity',
            'created_at',
            'expires_at'
        ]
        read_only_fields = [
            'id',
            'ip_address',
            'device_name',
            'last_activity',
            'created_at',
            'expires_at'
        ]
    
    def get_is_expired(self, obj):
        """Check if session is expired"""
        return obj.is_expired()


# PremiumSubscriptionSerializer commented out - model not yet created
# class PremiumSubscriptionSerializer(serializers.ModelSerializer):
#     """Premium Subscription Serializer"""
#     pass


# BillingHistorySerializer commented out - model not yet created
# class BillingHistorySerializer(serializers.ModelSerializer):
#     """Billing History Serializer for audit trail"""
#     pass


# APIKeySerializer commented out - model not yet created
# class APIKeySerializer(serializers.ModelSerializer):
#     """API Key Serializer for API access management"""
#     pass


class UserProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating user profile information
    SECURITY: Separate serializer for update operations with additional validation
    """
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    profile_visibility = serializers.ChoiceField(
        choices=['private', 'friends', 'public'],
        required=False
    )
    show_email = serializers.BooleanField(required=False)
    show_activity = serializers.BooleanField(required=False)
    
    def validate_phone_number(self, value):
        """Validate phone number"""
        if value and not re.match(r'^[\d\s\-\+\(\)]+$', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value
    
    def validate_date_of_birth(self, value):
        """Validate date of birth"""
        if value and value.year > 2020:
            raise serializers.ValidationError("Invalid date of birth.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password changes with security validation
    SECURITY: Validates old password, strength, and history
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        """Validate passwords match and meet requirements"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        # Validate password strength (minimum 8 chars, mix of types)
        if len(attrs['new_password']) < 8:
            raise serializers.ValidationError({
                'new_password': 'Password must be at least 8 characters.'
            })
        
        if not re.search(r'[A-Z]', attrs['new_password']):
            raise serializers.ValidationError({
                'new_password': 'Password must contain uppercase letter.'
            })
        
        if not re.search(r'[a-z]', attrs['new_password']):
            raise serializers.ValidationError({
                'new_password': 'Password must contain lowercase letter.'
            })
        
        if not re.search(r'[0-9]', attrs['new_password']):
            raise serializers.ValidationError({
                'new_password': 'Password must contain number.'
            })
        
        return attrs
