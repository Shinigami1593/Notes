from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Note, AuditLog
from .serializers import NoteSerializer
from .permissions import IsOwner
import logging

logger = logging.getLogger('security')


class NoteViewSet(viewsets.ModelViewSet):
    """
    Note ViewSet - Secure CRUD Operations
    
    SECURITY FEATURES:
    1. IsAuthenticated: Prevents unauthorized access
    2. IsOwner: Prevents IDOR attacks
    3. get_queryset: Filters by owner (never trust client)
    4. perform_create: Auto-assigns owner
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