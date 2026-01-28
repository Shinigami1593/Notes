"""
eSewa Payment Integration for Secure Notes

eSewa is a popular online payment gateway in Nepal.
Documentation: https://esewa.com.np/developers

This module handles eSewa payment integration with NPR (Nepali Rupees) pricing.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import hashlib
import logging
import requests

from authentication.models import UserProfile, Transaction, PremiumSubscription
from notes.models import AuditLog

logger = logging.getLogger('security')

# eSewa Configuration
ESEWA_MERCHANT_CODE = getattr(settings, 'ESEWA_MERCHANT_CODE', 'EPAYTEST')
ESEWA_PASSWORD = getattr(settings, 'ESEWA_PASSWORD', '')
ESEWA_API_URL = 'https://esewa.com.np/api/epay/transaction/status/'

# Nepali Price Map (in NPR)
SUBSCRIPTION_PRICES_NPR = {
    'free': {
        'name': 'नि:शुल्क',
        'amount': 0,
        'currency': 'NPR',
        'features': 10,  # max notes
    },
    'pro': {
        'name': 'Pro',
        'amount': 599,  # ~$5 USD
        'currency': 'NPR',
        'billing_cycle': 'monthly',
        'features': 'unlimited',
    },
    'enterprise': {
        'name': 'Enterprise',
        'amount': 1999,  # ~$15 USD
        'currency': 'NPR',
        'billing_cycle': 'monthly',
        'features': 'unlimited',
    }
}


def generate_esewa_signature(data, password):
    """
    Generate eSewa signature for payment verification
    
    Signature generation:
    1. Create string: total_amount + transaction_uuid + product_code + password
    2. Generate MD5 hash
    """
    message = f"{data.get('total_amount')}{data.get('transaction_uuid')}{data.get('product_code')}{password}"
    signature = hashlib.md5(message.encode()).hexdigest()
    return signature


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_esewa_payment(request):
    """
    Initiate eSewa payment for subscription upgrade
    
    Expected data:
    {
        'plan_type': 'pro' or 'enterprise',
        'amount': amount_in_npr,
        'order_id': unique_order_id
    }
    """
    try:
        plan_type = request.data.get('plan_type')
        amount = request.data.get('amount')
        order_id = request.data.get('order_id')
        
        # Validate plan type
        if plan_type not in SUBSCRIPTION_PRICES_NPR:
            return Response(
                {'error': 'Invalid plan type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate amount matches plan
        plan_price = SUBSCRIPTION_PRICES_NPR[plan_type]['amount']
        if int(amount) != plan_price:
            return Response(
                {'error': 'Amount does not match plan price'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create transaction record
        transaction_obj = Transaction.objects.create(
            user=request.user,
            amount=amount,
            currency='NPR',
            status='PENDING',
            subscription_tier=plan_type.upper(),
            payment_method='ESEWA',
            esewa_order_id=order_id
        )
        
        # Prepare eSewa payment data
        esewa_data = {
            'amt': str(amount),
            'psc': '0',
            'pdc': '0',
            'txAmt': str(amount),
            'tAmt': str(amount),
            'pid': order_id,  # Product/Order ID
            'scd': ESEWA_MERCHANT_CODE,
            'su': f"{request.build_absolute_uri('/').rstrip('/')}/billing?status=success",
            'fu': f"{request.build_absolute_uri('/').rstrip('/')}/billing?status=failure"
        }
        
        # Generate signature
        signature = generate_esewa_signature(esewa_data, ESEWA_PASSWORD) if ESEWA_PASSWORD else ''
        
        # Log transaction initiation
        logger.info(f"Payment initiated for user {request.user.username}: {order_id}")
        AuditLog.objects.create(
            user=request.user,
            action='PAYMENT_INITIATED',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details=f"eSewa payment initiated for {plan_type} plan: {order_id}"
        )
        
        return Response({
            'success': True,
            'transaction_id': str(transaction_obj.id),
            'esewa_data': esewa_data,
            'signature': signature,
            'esewa_url': 'https://esewa.com.np/epay/main'
        })
        
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response(
            {'error': 'Payment initiation failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_esewa_payment(request):
    """
    Verify eSewa payment using refId and orderId
    
    eSewa verification process:
    1. Get refId and orderId from client
    2. Call eSewa API to verify payment
    3. Update transaction status
    4. Activate subscription if successful
    """
    try:
        ref_id = request.data.get('ref_id')
        order_id = request.data.get('order_id')
        
        if not ref_id or not order_id:
            return Response(
                {'error': 'ref_id and order_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find transaction
        try:
            transaction_obj = Transaction.objects.get(
                user=request.user,
                esewa_order_id=order_id
            )
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify with eSewa API
        verification_successful = verify_with_esewa(ref_id, order_id)
        
        if verification_successful:
            # Update transaction status
            transaction_obj.status = 'COMPLETED'
            transaction_obj.esewa_ref_id = ref_id
            transaction_obj.save()
            
            # Activate subscription in both PremiumSubscription and UserProfile
            subscription, created = PremiumSubscription.objects.get_or_create(
                user=request.user
            )
            subscription.tier = transaction_obj.subscription_tier
            subscription.status = 'ACTIVE'
            subscription.billing_cycle_start = timezone.now()
            subscription.save()
            
            # Also update UserProfile subscription_tier for RBAC
            profile = UserProfile.objects.get(user=request.user)
            profile.subscription_tier = transaction_obj.subscription_tier
            profile.save()
            
            # Log successful payment
            logger.info(f"Payment verified for user {request.user.username}: {ref_id}")
            AuditLog.objects.create(
                user=request.user,
                action='PAYMENT_COMPLETED',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details=f"eSewa payment verified: {ref_id}, Subscription: {transaction_obj.subscription_tier}"
            )
            
            return Response({
                'success': True,
                'message': 'Payment verified successfully',
                'subscription_tier': transaction_obj.subscription_tier,
                'transaction_id': str(transaction_obj.id)
            })
        else:
            # Update transaction status to failed
            transaction_obj.status = 'FAILED'
            transaction_obj.save()
            
            logger.warning(f"Payment verification failed for user {request.user.username}: {ref_id}")
            
            return Response({
                'success': False,
                'message': 'Payment verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return Response(
            {'error': 'Payment verification failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def verify_with_esewa(ref_id, order_id):
    """
    Verify payment with eSewa API
    
    This would be called to confirm the payment with eSewa's servers.
    In production, implement proper signature verification.
    """
    try:
        # In production, implement actual eSewa API call
        # For now, we'll verify locally (INSECURE - implement properly)
        
        # TODO: Implement actual eSewa API verification
        # payload = {
        #     'rid': ref_id,
        # }
        # response = requests.post(ESEWA_API_URL, data=payload)
        # return response.status_code == 200
        
        # For testing, accept if ref_id exists
        return bool(ref_id)
        
    except Exception as e:
        logger.error(f"eSewa API verification error: {str(e)}")
        return False


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subscription_plans_npr(request):
    """
    Get available subscription plans with NPR pricing
    """
    plans = []
    for plan_type, plan_data in SUBSCRIPTION_PRICES_NPR.items():
        plans.append({
            'id': plan_type,
            'name': plan_data['name'],
            'amount': plan_data['amount'],
            'currency': plan_data['currency'],
            'billing_cycle': plan_data.get('billing_cycle', 'one-time'),
            'features': plan_data.get('features', 'standard'),
        })
    
    return Response({
        'plans': plans,
        'currency': 'NPR',
        'note': 'Prices in Nepali Rupees (NPR)'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_status(request):
    """
    Get user's payment and subscription status
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Get latest subscription
        try:
            subscription = PremiumSubscription.objects.get(user=request.user)
        except PremiumSubscription.DoesNotExist:
            subscription = None
        
        # Get latest transaction
        latest_transaction = Transaction.objects.filter(
            user=request.user
        ).order_by('-created_at').first()
        
        return Response({
            'user_id': request.user.id,
            'username': request.user.username,
            'subscription_tier': subscription.tier if subscription else 'FREE',
            'subscription_status': subscription.status if subscription else 'INACTIVE',
            'latest_transaction': {
                'id': str(latest_transaction.id) if latest_transaction else None,
                'status': latest_transaction.status if latest_transaction else None,
                'amount': str(latest_transaction.amount) if latest_transaction else None,
                'currency': latest_transaction.currency if latest_transaction else 'NPR',
                'created_at': latest_transaction.created_at.isoformat() if latest_transaction else None
            }
        })
        
    except Exception as e:
        logger.error(f"Payment status error: {str(e)}")
        return Response(
            {'error': 'Failed to retrieve payment status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_client_ip(request):
    """Extract client IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
