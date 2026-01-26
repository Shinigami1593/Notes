import hmac
import hashlib
import base64
from uuid import uuid4
from datetime import datetime

def generate_esewa_form_data(order_data):
    """
    Generate eSewa payment form data
    Docs: https://developer.esewa.com.np/pages/Epay-V2
    """
    total_amount = order_data.get('total_amount')
    transaction_uuid = order_data.get('transaction_uuid')
    product_code = order_data.get('product_code', 'EPAYTEST')
    success_url = order_data.get('success_url')
    failure_url = order_data.get('failure_url')
    
    secret_key = '8gBm/:&EnhH.1/q'  # Test Key
    
    # Format amount to 2 decimal places
    formatted_amount = f"{float(total_amount):.2f}"
    
    # Create signature string
    signature_string = f"total_amount={formatted_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    
    # Generate HMAC-SHA256
    signature = base64.b64encode(
        hmac.new(
            secret_key.encode(),
            signature_string.encode(),
            hashlib.sha256
        ).digest()
    ).decode()
    
    return {
        'amount': formatted_amount,
        'tax_amount': '0',
        'product_service_charge': '0',
        'product_delivery_charge': '0',
        'total_amount': formatted_amount,
        'transaction_uuid': transaction_uuid,
        'product_code': product_code,
        'success_url': success_url,
        'failure_url': failure_url,
        'signed_field_names': 'total_amount,transaction_uuid,product_code',
        'signature': signature
    }


def verify_esewa_payment(data):
    """
    Verify eSewa Response Signature
    This must use the 'signed_field_names' sent by eSewa
    """
    secret_key = '8gBm/:&EnhH.1/q'
    
    try:
        # Get the list of fields eSewa signed
        signed_field_names = data.get('signed_field_names', '')
        
        # Build the signature string dynamically
        fields = signed_field_names.split(',')
        signature_string_parts = [f"{field}={data.get(field)}" for field in fields]
        signature_string = ','.join(signature_string_parts)
        
        # Create expected signature
        expected_signature = base64.b64encode(
            hmac.new(
                secret_key.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        # Debug logs
        print("___ ESEWA VERIFY ___")
        print(f"Recvd String: {signature_string}")
        print(f"Recvd Sig:    {data.get('signature')}")
        print(f"Calc Sig:     {expected_signature}")
        
        return data.get('signature') == expected_signature
    
    except Exception as error:
        print(f"Signature Verification Error: {error}")
        return False


def generate_transaction_uuid():
    """Generate unique transaction UUID for eSewa"""
    timestamp = int(datetime.now().timestamp() * 1000)
    random_part = str(uuid4())[:8]
    return f"LUX-{timestamp}-{random_part}"
