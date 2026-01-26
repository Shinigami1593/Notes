from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
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
    new_filename = f"{uuid.uuid4()}{ext}"
    return f"user_{instance.owner.id}/{new_filename}"


class Note(models.Model):
    """
    Note Model - Core Security Features:
    - owner field enforces object-level permissions (IDOR prevention)
    - attachment field uses UUID naming (path traversal prevention)
    - created/modified timestamps for audit trail
    """
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notes',
        help_text="Note owner - enforces access control"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    attachment = models.FileField(
        upload_to=note_file_path,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
            )
        ],
        help_text="Optional file attachment with security validation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.owner.username}"


class AuditLog(models.Model):
    """
    Audit Trail Model - Security Monitoring
    - Tracks all security-relevant actions
    - Helps detect and investigate security incidents
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

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} - {self.action} - {self.timestamp}"