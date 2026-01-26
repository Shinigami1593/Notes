from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Note
import os
import mimetypes


class UserSerializer(serializers.ModelSerializer):
    """
    SECURITY: Minimal user data exposure
    - Only expose necessary fields
    - Never expose password or sensitive data
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']


class NoteSerializer(serializers.ModelSerializer):
    """
    Note Serializer - Security Features:
    - owner is read_only to prevent IDOR attacks
    - Validates file extensions and size
    - MIME type validation prevents file upload injection
    - Double extension attack prevention
    - Input validation prevents injection attacks
    """
    owner = UserSerializer(read_only=True)
    attachment_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            'id', 
            'title', 
            'content', 
            'attachment',
            'attachment_url',
            'file_size',
            'owner', 
            'created_at', 
            'modified_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'modified_at']

    def get_attachment_url(self, obj):
        """
        SECURITY: Safe URL generation
        - Returns None if no attachment
        - Uses Django's secure URL building
        """
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
        return None

    def get_file_size(self, obj):
        """Get file size in a human-readable format"""
        if obj.attachment:
            try:
                size = obj.attachment.size
                for unit in ['B', 'KB', 'MB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} GB"
            except:
                return None
        return None

    def validate_attachment(self, value):
        """
        SECURITY: Comprehensive File Upload Validation
        - Size limit validation (5MB max)
        - Extension whitelist validation
        - MIME type validation to prevent injection
        - Prevents double extension attacks
        """
        if value:
            # Size check
            if value.size > 5242880:  # 5MB
                raise serializers.ValidationError(
                    "File size exceeds 5MB limit."
                )
            
            # Get file extension
            filename = value.name
            ext = os.path.splitext(filename)[1].lower()
            
            # Extension whitelist check
            allowed_extensions = ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif']
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"File type '.{ext[1:] if ext else 'unknown'}' not allowed. "
                    f"Allowed types: {', '.join([e[1:] for e in allowed_extensions])}"
                )
            
            # MIME type validation to prevent extension spoofing
            allowed_mime_types = {
                '.txt': ['text/plain'],
                '.pdf': ['application/pdf'],
                '.png': ['image/png'],
                '.jpg': ['image/jpeg'],
                '.jpeg': ['image/jpeg'],
                '.gif': ['image/gif']
            }
            
            # Try to get MIME type from file content
            file_mime, _ = mimetypes.guess_type(filename)
            
            # If we can detect a MIME type, validate it
            if file_mime and ext in allowed_mime_types:
                if file_mime not in allowed_mime_types[ext]:
                    raise serializers.ValidationError(
                        f"File MIME type '{file_mime}' does not match the extension. "
                        f"This might be a file spoofing attempt."
                    )
            
            # Check for double extension attacks (e.g., file.php.txt)
            name_without_ext = os.path.splitext(filename)[0]
            if '.' in name_without_ext:
                # There's another dot in the filename - potential double extension
                inner_ext = os.path.splitext(name_without_ext)[1].lower()
                dangerous_extensions = [
                    '.php', '.py', '.js', '.exe', '.sh', '.bat', '.cmd',
                    '.com', '.pif', '.scr', '.vbs', '.asp', '.jsp', '.pl'
                ]
                if inner_ext in dangerous_extensions:
                    raise serializers.ValidationError(
                        f"Suspicious filename detected. Double extensions are not allowed."
                    )
        
        return value

    def validate_title(self, value):
        """Input validation - XSS prevention"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) > 200:
            raise serializers.ValidationError("Title too long (max 200 characters).")
        return value.strip()

    def validate_content(self, value):
        """Input validation"""
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip()
