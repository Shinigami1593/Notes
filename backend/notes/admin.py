from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Note, AuditLog


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """
    Custom Note Admin Interface
    
    FEATURES:
    - Clean display of all note fields
    - Search and filter capabilities
    - Read-only timestamps
    - Owner information clearly visible
    """
    list_display = ['id', 'title', 'owner_username', 'has_attachment', 'created_at', 'modified_at']
    list_filter = ['created_at', 'modified_at', 'owner']
    search_fields = ['title', 'content', 'owner__username']
    readonly_fields = ['created_at', 'modified_at', 'id']
    
    fieldsets = (
        ('Note Information', {
            'fields': ('id', 'title', 'content', 'owner')
        }),
        ('Attachment', {
            'fields': ('attachment',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )
    
    def owner_username(self, obj):
        """Display owner username in list view"""
        return obj.owner.username
    owner_username.short_description = 'Owner'
    owner_username.admin_order_field = 'owner__username'
    
    def has_attachment(self, obj):
        """Show if note has attachment"""
        return bool(obj.attachment)
    has_attachment.short_description = 'Attachment'
    has_attachment.boolean = True
    
    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('owner')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Audit Log Admin Interface
    
    FEATURES:
    - Security event monitoring
    - Filter by action type
    - Search by user and IP
    - Read-only (no modifications)
    """
    list_display = ['id', 'user_username', 'action', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'ip_address', 'details']
    readonly_fields = ['user', 'action', 'ip_address', 'user_agent', 'details', 'timestamp']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('user', 'action', 'timestamp')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Additional Information', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def user_username(self, obj):
        """Display username or 'Anonymous'"""
        return obj.user.username if obj.user else 'Anonymous'
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'
    
    def has_add_permission(self, request):
        """Prevent manual log creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent log deletion"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make logs read-only"""
        return False


# Customize User Admin
class CustomUserAdmin(BaseUserAdmin):
    """
    Enhanced User Admin
    
    Shows note count for each user
    """
    list_display = BaseUserAdmin.list_display + ('note_count', 'date_joined')
    
    def note_count(self, obj):
        """Display number of notes per user"""
        return obj.notes.count()
    note_count.short_description = 'Notes'

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site headers
admin.site.site_header = "Secure Notes Administration"
admin.site.site_title = "Secure Notes Admin"
admin.site.index_title = "Welcome to Secure Notes Admin Portal"

