import json
import random
import time

def lambda_handler(event, context):
    """
    Simulate payment processing
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        order_id = event.get('order_id')
        total_amount = event.get('total_amount', 0)
        current_time = int(time.time())
        
        # Convert order_id to string for slicing
        order_id_str = str(order_id)
        
        # Simulate payment processing delay
        time.sleep(2)
        
        # Simulate payment success/failure (90% success rate)
        payment_success = random.random() < 0.9
        
        if payment_success:
            payment_status = 'success'
            transaction_id = f"TXN-{order_id_str[:8] if len(order_id_str) >= 8 else order_id_str}-{current_time}"
            message = 'Payment processed successfully'
        else:
            payment_status = 'failed'
            transaction_id = None
            message = 'Payment processing failed'
        
        response = {
            'order_id': order_id,
            'paymentStatus': payment_status,
            'transaction_id': transaction_id,
            'amount': total_amount,
            'message': message,
            'timestamp': current_time,
            'processed_at': current_time  # Tambahkan field ini
        }
        
        print(f"Returning response: {json.dumps(response)}")
        return response
        
    except Exception as e:
        print(f"Error processing payment: {str(e)}")
        current_time = int(time.time())
        error_response = {
            'order_id': event.get('order_id'),
            'paymentStatus': 'error',
            'transaction_id': None,
            'message': f'Payment error: {str(e)}',
            'timestamp': current_time,
            'processed_at': current_time  # Tambahkan field ini
        }
        print(f"Returning error response: {json.dumps(error_response)}")
        return error_response