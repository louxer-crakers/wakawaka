import json
import os
import psycopg2
import boto3
from datetime import datetime

# Environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

eventbridge = boto3.client('events')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def lambda_handler(event, context):
    print(f"Updating inventory for event: {json.dumps(event)}")
    
    # Convert order_id to string if it's integer
    order_id = str(event.get('order_id')) if event.get('order_id') else None
    items = event.get('items', [])
    
    if not order_id:
        return {
            'order_id': order_id,
            'inventoryStatus': 'failed',
            'message': 'Order ID is required',
            'updated_products': [],
            'low_stock_alerts': []
        }
    
    if not items:
        # If items not in event, get from database
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT product_id, quantity
                FROM order_items
                WHERE order_id = %s
            """, (order_id,))
            
            items = []
            for row in cur.fetchall():
                items.append({
                    'productId': row[0],
                    'quantity': row[1]
                })
            
            cur.close()
            conn.close()
            
            if not items:
                return {
                    'order_id': order_id,
                    'inventoryStatus': 'failed',
                    'message': 'No items found for this order',
                    'updated_products': [],
                    'low_stock_alerts': []
                }
        except Exception as e:
            print(f"Error fetching order items: {str(e)}")
            return {
                'order_id': order_id,
                'inventoryStatus': 'failed',
                'message': f'Error fetching items: {str(e)}',
                'updated_products': [],
                'low_stock_alerts': []
            }
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        updated_products = []
        low_stock_alerts = []
        
        for item in items:
            # Handle both productId and productName
            product_id = item.get('productId') or item.get('product_id')
            product_name = item.get('productName') or item.get('product_name')
            quantity = item.get('quantity', 0)
            
            # If only productName is provided, find product_id
            if not product_id and product_name:
                cur.execute("""
                    SELECT product_id FROM inventory 
                    WHERE product_name = %s
                """, (product_name,))
                
                row = cur.fetchone()
                if row:
                    product_id = row[0]
            
            if not product_id:
                print(f"Product not found: {product_name or 'unknown'}")
                continue
            
            # Check current stock
            cur.execute("""
                SELECT stock_quantity, product_name
                FROM inventory
                WHERE product_id = %s
                FOR UPDATE
            """, (product_id,))
            
            result = cur.fetchone()
            if not result:
                print(f"Product {product_id} not found in inventory")
                continue
            
            current_stock, db_product_name = result
            
            # Check if sufficient stock
            if current_stock < quantity:
                conn.rollback()
                return {
                    'order_id': order_id,
                    'inventoryStatus': 'failed',
                    'message': f'Insufficient stock for product {db_product_name}',
                    'product_id': product_id,
                    'available': current_stock,
                    'requested': quantity,
                    'updated_products': [],
                    'low_stock_alerts': []
                }
            
            # Update inventory
            new_stock = current_stock - quantity
            cur.execute("""
                UPDATE inventory
                SET stock_quantity = %s,
                    updated_at = %s
                WHERE product_id = %s
            """, (new_stock, datetime.now(), product_id))
            
            updated_products.append({
                'product_id': product_id,
                'product_name': db_product_name,
                'previous_stock': current_stock,
                'new_stock': new_stock,
                'quantity_sold': quantity
            })
            
            # Check for low stock (threshold: 10 units)
            if new_stock <= 10:
                low_stock_alerts.append({
                    'product_id': product_id,
                    'product_name': db_product_name,
                    'current_stock': new_stock
                })
        
        # Update order status
        cur.execute("""
            UPDATE orders
            SET status = %s, updated_at = %s
            WHERE order_id = %s
        """, ('inventory_updated', datetime.now(), order_id))
        
        conn.commit()
        
        # Send low stock events to EventBridge
        if low_stock_alerts:
            for alert in low_stock_alerts:
                try:
                    eventbridge.put_events(
                        Entries=[{
                            'Source': 'order.system',
                            'DetailType': 'LowStock',
                            'Detail': json.dumps({
                                'product_id': alert['product_id'],
                                'product_name': alert['product_name'],
                                'current_stock': alert['current_stock'],
                                'timestamp': datetime.now().isoformat()
                            })
                        }]
                    )
                except Exception as e:
                    print(f"Error sending low stock event: {str(e)}")
        
        print(f"Inventory updated successfully for order {order_id}")
        
        return {
            'order_id': order_id,
            'inventoryStatus': 'success',
            'message': 'Inventory updated successfully',
            'updated_products': updated_products,
            'low_stock_alerts': low_stock_alerts,
            'updated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating inventory: {str(e)}")
        return {
            'order_id': order_id,
            'inventoryStatus': 'failed',
            'message': f'Inventory update error: {str(e)}',
            'updated_products': [],
            'low_stock_alerts': []
        }
    finally:
        cur.close()
        conn.close()