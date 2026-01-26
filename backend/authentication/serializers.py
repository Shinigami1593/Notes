from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
import re


class RegisterSerializer(serializers.ModelSerializer):
    """
    Registration Serializer - Security Features:
    - Password validation using Django validators
    - Password confirmation check
    - Prevents weak passwords (OWASP)
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
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, attrs):
        """
        SECURITY: Password validation
        - Ensures passwords match
        - Prevents registration with weak passwords
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_username(self, value):
        """Username validation"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        return value

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Login Serializer - Input Validation
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    two_factor_token = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=6
    )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Change Password Serializer - Security validation
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )


class PasswordStrengthSerializer(serializers.Serializer):
    """
    Password Strength Check Serializer
    Provides real-time feedback on password strength
    """
    password = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        """
        Calculate password strength and provide feedback
        Returns the password value (not a dict)
        """
        # This method just validates the password field
        # Don't return a dict here, just return the value
        return value

    def validate(self, attrs):
        """
        Calculate password strength and provide feedback
        This is where we analyze the password
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

        # Return the result in attrs format
        return {
            'strength': strength_level,
            'feedback': feedback,
            'score': strength
        }


class TwoFactorSetupSerializer(serializers.Serializer):
    """
    Two-Factor Authentication Setup Serializer
    """
    enable = serializers.BooleanField(required=True)


class TwoFactorVerifySerializer(serializers.Serializer):
    """
    Two-Factor Authentication Verification Serializer
    """
    token = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6
    )

    def validate_token(self, value):
        """Ensure token is 6 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("Token must be 6 digits")
        return value