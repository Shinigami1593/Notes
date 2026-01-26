from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .esewa import (
    generate_esewa_form_data,
    verify_esewa_payment,
    generate_transaction_uuid
)
import logging
import json
import base64

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_esewa_payment(request):
    """
    Initiate eSewa payment for subscription upgrade
    """
    try:
        plan_id = request.data.get('plan_id')
        
        # Plan pricing
        plans = {
            'pro': {
                'name': 'Pro Plan',
                'amount': 9.99,
            },
            'enterprise': {
                'name': 'Enterprise Plan',
                'amount': 29.99,
            }
        }
        
        if plan_id not in plans:
            return Response(
                {'success': False, 'message': 'Invalid plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan = plans[plan_id]
        total_amount = plan['amount']
        
        # Generate transaction UUID
        transaction_uuid = generate_transaction_uuid()
        
        # Determine URLs based on environment
        protocol = request.scheme
        host = request.get_host()
        
        success_url = f"{protocol}://{host}/api/payments/esewa/success"
        failure_url = f"{protocol}://{host}/api/payments/esewa/failure"
        
        # Generate eSewa form data
        esewa_data = generate_esewa_form_data({
            'total_amount': total_amount,
            'transaction_uuid': transaction_uuid,
            'product_code': 'EPAYTEST',
            'success_url': success_url,
            'failure_url': failure_url
        })
        
        # Store transaction info in session or database for verification
        request.session['esewa_transaction'] = {
            'uuid': transaction_uuid,
            'plan_id': plan_id,
            'amount': total_amount,
            'user_id': str(request.user.id)
        }
        request.session.save()
        
        return Response({
            'success': True,
            'data': {
                'formData': esewa_data,
                'esewaUrl': 'https://rc-epay.esewa.com.np/api/epay/main/v2/form',
                'transactionUUID': transaction_uuid
            }
        })
    
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return Response(
            {'success': False, 'message': 'Payment initiation failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
def esewa_success(request):
    """
    eSewa payment success callback
    """
    try:
        # Get response data from query parameters or POST body
        if request.method == 'POST':
            response_data = request.data
        else:
            response_data = request.query_params.dict()
        
        # Validate callback origin
        referer = request.META.get('HTTP_REFERER', '')
        if 'esewa.com.np' not in referer:
            logger.warning(f"Invalid callback origin: {referer}")
            return Response(
                {'success': False, 'message': 'Invalid callback origin'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Decode eSewa base64 data if present
        decoded_data = response_data
        if 'data' in response_data:
            try:
                buff = base64.b64decode(response_data['data'])
                decoded_data = json.loads(buff.decode('utf-8'))
            except:
                pass
        
        # Verify signature
        if not verify_esewa_payment(decoded_data):
            logger.warning(f"Invalid payment signature for transaction: {decoded_data.get('transaction_uuid')}")
            return Response(
                {'success': False, 'message': 'Invalid signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get transaction info from session
        esewa_transaction = request.session.get('esewa_transaction', {})
        transaction_uuid = decoded_data.get('transaction_uuid')
        
        if transaction_uuid != esewa_transaction.get('uuid'):
            logger.warning(f"Transaction UUID mismatch")
            return Response(
                {'success': False, 'message': 'Transaction UUID mismatch'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Update user subscription in database
        # This is where you would update the user's subscription plan
        plan_id = esewa_transaction.get('plan_id')
        user_id = esewa_transaction.get('user_id')
        
        logger.info(f"Payment successful for user {user_id}, plan {plan_id}")
        
        # Clear session
        if 'esewa_transaction' in request.session:
            del request.session['esewa_transaction']
            request.session.save()
        
        return Response({
            'success': True,
            'message': 'Payment successful',
            'transaction_uuid': transaction_uuid
        })
    
    except Exception as e:
        logger.error(f"Payment callback error: {str(e)}")
        return Response(
            {'success': False, 'message': 'Payment processing failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
def esewa_failure(request):
    """
    eSewa payment failure callback
    """
    try:
        if request.method == 'POST':
            response_data = request.data
        else:
            response_data = request.query_params.dict()
        
        transaction_uuid = response_data.get('transaction_uuid')
        
        # If data is base64 encoded, decode it
        if 'data' in response_data:
            try:
                buff = base64.b64decode(response_data['data'])
                decoded_data = json.loads(buff.decode('utf-8'))
                transaction_uuid = decoded_data.get('transaction_uuid')
            except:
                pass
        
        logger.warning(f"Payment failed for transaction: {transaction_uuid}")
        
        # Clear session
        if 'esewa_transaction' in request.session:
            del request.session['esewa_transaction']
            request.session.save()
        
        return Response({
            'success': False,
            'message': 'Payment failed',
            'transaction_uuid': transaction_uuid
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Payment failure handler error: {str(e)}")
        return Response(
            {'success': False, 'message': 'Error processing failure'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request, transaction_uuid):
    """
    Verify payment status
    """
    try:
        # TODO: Get payment status from database
        # For now, return success if payment was processed
        
        esewa_transaction = request.session.get('esewa_transaction', {})
        
        # Payment is verified if session transaction was cleared (means success callback happened)
        is_verified = not esewa_transaction
        
        return Response({
            'success': True,
            'data': {
                'verified': is_verified,
                'transaction_uuid': transaction_uuid
            }
        })
    
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return Response(
            {'success': False, 'message': 'Verification failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
