from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Note, AuditLog
from authentication.models import UserProfile, Transaction, PremiumSubscription


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
    
    Shows note count and subscription tier for each user
    """
    list_display = BaseUserAdmin.list_display + ('note_count', 'subscription_tier', 'date_joined')
    
    def note_count(self, obj):
        """Display number of notes per user"""
        return obj.notes.count()
    note_count.short_description = 'Notes'
    
    def subscription_tier(self, obj):
        """Display user's subscription tier"""
        try:
            return obj.profile.subscription_tier
        except:
            return 'N/A'
    subscription_tier.short_description = 'Tier'

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    User Profile Admin - RBAC Management
    
    FEATURES:
    - View all user profiles
    - Change subscription tiers (for admin override)
    - Monitor 2FA status
    - Track login activity
    """
    list_display = ['user_username', 'subscription_tier', 'two_factor_enabled', 'last_login_ip', 'created_at']
    list_filter = ['subscription_tier', 'two_factor_enabled', 'created_at']
    search_fields = ['user__username', 'user__email', 'last_login_ip']
    list_editable = ['subscription_tier']  # Allow admin to change tier
    readonly_fields = ['created_at', 'updated_at', 'password_changed_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'subscription_tier')
        }),
        ('Security', {
            'fields': ('two_factor_enabled', 'two_factor_secret', 'password_changed_at', 'force_password_change', 'account_locked_until')
        }),
        ('Login Tracking', {
            'fields': ('last_login_ip', 'last_login_user_agent', 'failed_login_attempts', 'last_failed_login'),
            'classes': ('collapse',)
        }),
        ('Profile Information', {
            'fields': ('bio', 'avatar_url', 'phone_number', 'date_of_birth'),
            'classes': ('collapse',)
        }),
        ('Privacy Settings', {
            'fields': ('profile_visibility', 'show_email', 'show_activity'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('notify_login_attempts', 'notify_password_changes', 'notify_2fa_changes', 'notify_new_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_username(self, obj):
        """Display username"""
        return obj.user.username
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Transaction Admin - Payment & Subscription Management
    
    FEATURES:
    - View all payment transactions
    - Filter by status and payment method
    - Monitor subscription changes
    - Audit payment history
    """
    list_display = ['id', 'user_username', 'payment_method', 'amount_display', 'subscription_tier', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'subscription_tier', 'created_at']
    search_fields = ['user__username', 'user__email', 'esewa_ref_id', 'stripe_payment_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('id', 'user', 'transaction_type', 'status')
        }),
        ('Amount & Currency', {
            'fields': ('amount', 'currency'),
            'description': 'Amount is stored in cents/paisa'
        }),
        ('Subscription Info', {
            'fields': ('subscription_tier', 'billing_period_start', 'billing_period_end')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'stripe_payment_id', 'esewa_order_id', 'esewa_ref_id')
        }),
        ('Security', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('description', 'metadata', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_username(self, obj):
        """Display username"""
        return obj.user.username
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'
    
    def amount_display(self, obj):
        """Display formatted amount"""
        return obj.get_amount_display()
    amount_display.short_description = 'Amount'


@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    """
    Premium Subscription Admin - RBAC & Subscription Management
    
    FEATURES:
    - View all active subscriptions
    - Change subscription status
    - Monitor billing cycles
    - Admin override capability
    """
    list_display = ['user_username', 'tier', 'status', 'is_active_display', 'billing_cycle_end', 'updated_at']
    list_filter = ['tier', 'status', 'updated_at']
    search_fields = ['user__username', 'user__email']
    list_editable = ['tier', 'status']  # Allow admin to change directly
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('user', 'tier', 'status')
        }),
        ('Billing Cycle', {
            'fields': ('billing_cycle_start', 'billing_cycle_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_username(self, obj):
        """Display username"""
        return obj.user.username
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'
    
    def is_active_display(self, obj):
        """Display if subscription is active"""
        return obj.is_active()
    is_active_display.short_description = 'Active'
    is_active_display.boolean = True


# Customize admin site headers
admin.site.site_header = "Secure Notes Administration"
admin.site.site_title = "Secure Notes Admin"
admin.site.index_title = "Welcome to Secure Notes Admin Portal"
