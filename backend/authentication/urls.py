from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register_view,
    login_view,
    logout_view,
    current_user_view,
    change_password_view,
    check_password_strength,
    setup_two_factor,
    verify_two_factor,
)
from .views_profile import (
    profile_view,
    sessions_view,
    TransactionViewSet,
)
from .views_esewa import (
    initiate_esewa_payment,
    verify_esewa_payment,
    get_subscription_plans_npr,
    get_payment_status,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
# SubscriptionViewSet, BillingHistoryViewSet, APIKeyViewSet commented out - models not yet created

urlpatterns = [
    # Authentication endpoints
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('user/', current_user_view, name='current-user'),
    path('change-password/', change_password_view, name='change-password'),
    path('password-strength/', check_password_strength, name='password-strength'),
    path('2fa/setup/', setup_two_factor, name='2fa-setup'),
    path('2fa/verify/', verify_two_factor, name='2fa-verify'),
    
    # Profile endpoints
    path('profile/', profile_view, name='profile'),
    path('sessions/', sessions_view, name='sessions'),
    
    # eSewa Payment Integration (Nepali Payment Gateway)
    path('payments/esewa/initiate/', initiate_esewa_payment, name='esewa-initiate'),
    path('payments/esewa/verify/', verify_esewa_payment, name='esewa-verify'),
    path('payments/plans/npr/', get_subscription_plans_npr, name='plans-npr'),
    path('payments/status/', get_payment_status, name='payment-status'),
    
    # ViewSet endpoints
    path('', include(router.urls)),
]
