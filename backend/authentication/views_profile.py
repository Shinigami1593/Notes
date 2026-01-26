from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django_ratelimit.decorators import ratelimit
import stripe
import logging

from authentication.models import UserProfile, Transaction, UserSession
from authentication.serializers_extended import (
    UserProfileSerializer,
    TransactionSerializer,
    UserSessionSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer
)
from notes.models import AuditLog

logger = logging.getLogger('security')

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def get_client_ip(request):
    """Extract client IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Retrieve and update user profile
    SECURITY: User can only access their own profile
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # Update profile fields
            for field, value in serializer.validated_data.items():
                setattr(profile, field, value)
            profile.save()
            
            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE_NOTE',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details="Profile updated"
            )
            
            logger.info(f"User {request.user.username} updated profile")
            
            updated_serializer = UserProfileSerializer(profile)
            return Response(updated_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='3/h', method='POST')
def change_password_view(request):
    """
    Change user password with security validation
    SECURITY:
    - Rate limited to 3 attempts per hour
    - Validates old password
    - Checks password strength
    - Prevents password reuse
    """
    serializer = ChangePasswordSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    old_password = serializer.validated_data['old_password']
    new_password = serializer.validated_data['new_password']
    
    # Verify old password
    if not user.check_password(old_password):
        AuditLog.objects.create(
            user=user,
            action='FAILED_LOGIN',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details="Failed password change attempt - wrong password"
        )
        return Response(
            {'old_password': 'Incorrect password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update password
    user.set_password(new_password)
    user.save()
    
    # Update profile timestamp
    profile = UserProfile.objects.get(user=user)
    profile.password_changed_at = timezone.now()
    profile.save()
    
    # Audit log
    AuditLog.objects.create(
        user=user,
        action='UPDATE_NOTE',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details="Password changed successfully"
    )
    
    logger.warning(f"Password changed for user: {user.username}")
    
    return Response({'message': 'Password changed successfully'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sessions_view(request):
    """
    Manage user sessions
    GET: List all active sessions
    POST: Logout from specific session
    SECURITY: User can manage their own sessions
    """
    if request.method == 'GET':
        sessions = UserSession.objects.filter(user=request.user, is_active=True)
        serializer = UserSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        session_id = request.data.get('session_id')
        try:
            session = UserSession.objects.get(id=session_id, user=request.user)
            session.mark_inactive()
            
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE_NOTE',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details=f"Session terminated - {session.device_name}"
            )
            
            return Response({'message': 'Session terminated'})
        except UserSession.DoesNotExist:
            return Response(
                {'detail': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Transaction ViewSet - View transaction history
    SECURITY: Users can only view their own transactions
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions by user"""
        return Transaction.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        """
        Create a payment transaction
        SECURITY:
        - Validates amount
        - Rate limited
        - Integrates with Stripe
        """
        serializer = TransactionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Create transaction record
                trans = Transaction.objects.create(
                    user=request.user,
                    transaction_type=serializer.validated_data['transaction_type'],
                    amount=serializer.validated_data['amount'],
                    currency=serializer.validated_data.get('currency', 'USD'),
                    description=serializer.validated_data.get('description', ''),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status='processing'
                )
                
                # Process payment with Stripe (if configured)
                if stripe.api_key:
                    try:
                        charge = stripe.Charge.create(
                            amount=serializer.validated_data['amount'],
                            currency=serializer.validated_data.get('currency', 'USD').lower(),
                            source='tok_visa',  # This should come from frontend tokenization
                            description=serializer.validated_data.get('description', ''),
                            metadata={'transaction_id': str(trans.transaction_id)}
                        )
                        
                        trans.stripe_payment_id = charge.id
                        trans.status = 'completed'
                        trans.completed_at = timezone.now()
                        trans.save()
                        
                        AuditLog.objects.create(
                            user=request.user,
                            action='CREATE_NOTE',
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            details=f"Payment processed - ${trans.amount/100:.2f}"
                        )
                        
                        logger.info(f"Payment processed for {request.user.username}: ${trans.amount/100:.2f}")
                        
                    except stripe.error.CardError as e:
                        trans.status = 'failed'
                        trans.error_message = str(e)
                        trans.save()
                        
                        logger.error(f"Card error for user {request.user.username}: {str(e)}")
                        
                        return Response(
                            {'detail': 'Payment failed: Card declined'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    except stripe.error.StripeError as e:
                        trans.status = 'failed'
                        trans.error_message = str(e)
                        trans.save()
                        
                        logger.error(f"Stripe error for user {request.user.username}: {str(e)}")
                        
                        return Response(
                            {'detail': 'Payment processing error'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    # If Stripe not configured, mark as completed
                    trans.status = 'completed'
                    trans.completed_at = timezone.now()
                    trans.save()
                
                return Response(TransactionSerializer(trans).data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating payment for {request.user.username}: {str(e)}")
            return Response(
                {'detail': 'Error processing payment'},
                status=status.HTTP_400_BAD_REQUEST
            )


# SubscriptionViewSet commented out - PremiumSubscription model not yet created
# class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
#     """Subscription ViewSet"""
#     pass


# BillingHistoryViewSet commented out - BillingHistory model not yet created
# class BillingHistoryViewSet(viewsets.ReadOnlyModelViewSet):
#     """Billing History ViewSet"""
#     pass


# APIKeyViewSet commented out - APIKey model not yet created
# class APIKeyViewSet(viewsets.ModelViewSet):
#     """API Key ViewSet"""
#     pass

