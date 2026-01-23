import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid

# Environment variables
DB_HOST = os.environ['DB_HOST']
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
S3_BUCKET = os.environ['S3_BUCKET']
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']

s3_client = boto3.client('s3')
sfn_client = boto3.client('stepfunctions')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def lambda_handler(event, context):
    print(f"Event received: {json.dumps(event)}")
    
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    try:
        if http_method == 'POST' and path == '/orders':
            return create_order(event)
        elif http_method == 'GET' and path == '/orders':
            return list_orders(event)
        elif http_method == 'GET' and '/orders/' in path:
            order_id = event['pathParameters']['id']
            return get_order(order_id)
        elif http_method == 'PUT' and '/orders/' in path:
            order_id = event['pathParameters']['id']
            return update_order(order_id, event)
        elif http_method == 'DELETE' and '/orders/' in path:
            order_id = event['pathParameters']['id']
            return delete_order(order_id)
        elif http_method == 'GET' and '/status/' in path:
            execution_arn = event['pathParameters']['id']
            return get_workflow_status(execution_arn)
        else:
            return response(400, {'message': 'Invalid request'})
    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {'message': 'Internal server error', 'error': str(e)})

def create_order(event):
    body = json.loads(event['body'])
    
    # Validate required fields
    required_fields = ['customer_id', 'items']
    for field in required_fields:
        if field not in body:
            return response(400, {'message': f'Missing required field: {field}'})
    
    order_id = str(uuid.uuid4())
    customer_id = body['customer_id']
    items = body['items']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Calculate total amount
        total_amount = 0
        for item in items:
            cur.execute("SELECT price FROM inventory WHERE product_id = %s", (item['product_id'],))
            result = cur.fetchone()
            if result:
                total_amount += result[0] * item['quantity']
        
        # Insert order
        cur.execute("""
            INSERT INTO orders (order_id, customer_id, total_amount, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, customer_id, total_amount, 'pending', datetime.now()))
        
        # Insert order items
        for item in items:
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                SELECT %s, %s, %s, price FROM inventory WHERE product_id = %s
            """, (order_id, item['product_id'], item['quantity'], item['product_id']))
        
        conn.commit()
        
        # Save order to S3
        s3_key = f"orders/{order_id}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps({
                'order_id': order_id,
                'customer_id': customer_id,
                'items': items,
                'total_amount': total_amount,
                'created_at': datetime.now().isoformat()
            })
        )
        
        # Start Step Functions workflow
        execution_response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"order-{order_id}",
            input=json.dumps({
                'order_id': order_id,
                'customer_id': customer_id,
                'total_amount': total_amount
            })
        )
        
        return response(201, {
            'message': 'Order created successfully',
            'order_id': order_id,
            'execution_arn': execution_response['executionArn']
        })
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def list_orders(event):
    params = event.get('queryStringParameters', {}) or {}
    page = int(params.get('page', 1))
    limit = int(params.get('limit', 10))
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT order_id, customer_id, total_amount, status, created_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        orders = []
        for row in cur.fetchall():
            orders.append({
                'order_id': row[0],
                'customer_id': row[1],
                'total_amount': float(row[2]),
                'status': row[3],
                'created_at': row[4].isoformat()
            })
        
        cur.execute("SELECT COUNT(*) FROM orders")
        total = cur.fetchone()[0]
        
        return response(200, {
            'orders': orders,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
    finally:
        cur.close()
        conn.close()

def get_order(order_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT order_id, customer_id, total_amount, status, created_at
            FROM orders
            WHERE order_id = %s
        """, (order_id,))
        
        row = cur.fetchone()
        if not row:
            return response(404, {'message': 'Order not found'})
        
        cur.execute("""
            SELECT product_id, quantity, price
            FROM order_items
            WHERE order_id = %s
        """, (order_id,))
        
        items = []
        for item_row in cur.fetchall():
            items.append({
                'product_id': item_row[0],
                'quantity': item_row[1],
                'price': float(item_row[2])
            })
        
        return response(200, {
            'order_id': row[0],
            'customer_id': row[1],
            'total_amount': float(row[2]),
            'status': row[3],
            'created_at': row[4].isoformat(),
            'items': items
        })
    finally:
        cur.close()
        conn.close()

def update_order(order_id, event):
    body = json.loads(event['body'])
    status = body.get('status')
    
    if not status:
        return response(400, {'message': 'Status is required'})
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE orders
            SET status = %s, updated_at = %s
            WHERE order_id = %s
        """, (status, datetime.now(), order_id))
        
        if cur.rowcount == 0:
            return response(404, {'message': 'Order not found'})
        
        conn.commit()
        
        return response(200, {
            'message': 'Order updated successfully',
            'order_id': order_id,
            'status': status
        })
    finally:
        cur.close()
        conn.close()

def delete_order(order_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
        cur.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
        
        if cur.rowcount == 0:
            return response(404, {'message': 'Order not found'})
        
        conn.commit()
        
        return response(200, {
            'message': 'Order deleted successfully',
            'order_id': order_id
        })
    finally:
        cur.close()
        conn.close()

def get_workflow_status(execution_arn):
    try:
        execution = sfn_client.describe_execution(executionArn=execution_arn)
        
        return response(200, {
            'execution_arn': execution_arn,
            'status': execution['status'],
            'start_date': execution['startDate'].isoformat(),
            'stop_date': execution.get('stopDate', '').isoformat() if execution.get('stopDate') else None
        })
    except Exception as e:
        return response(404, {'message': 'Execution not found', 'error': str(e)})

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }