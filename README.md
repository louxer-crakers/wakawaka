# Order Management API

A RESTful API for managing orders with database storage, S3 backup, and AWS Step Functions workflow integration.

##  Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Setup & Deployment](#setup--deployment)

## Overview

This API provides a complete order management system with the following features:
-  Create orders with automatic price calculation
-  List orders with pagination
-  Retrieve detailed order information
-  Update order status
-  Delete orders
-  Check Step Functions workflow status
-  Automatic S3 backup of orders
-  Step Functions workflow triggering

## API Endpoints

### Base URL
\
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
\

### 1. Create Order
**POST** \/orders

Creates a new order, saves to database and S3, and starts a Step Functions workflow.

**Request:**<br/>
\
curl -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "customer_id": "CUST001",
    "items": [
      {"product_id": "PROD001", "quantity": 2},
      {"product_id": "PROD002", "quantity": 1}
    ]
  }' \
  https://your-api-id.execute-api.region.amazonaws.com/stage/orders
\

**Response (201 Created):**\
\\json
{
  "message": "Order created successfully",\
  "order_id": "550e8400-e29b-41d4-a716-446655440000",\
  "execution_arn": "arn:aws:states:us-east-1:123456789012:execution:OrderProcessingStateMachine:550e8400-e29b-41d4-a716-446655440000",\
  "note": "Save this execution_arn to check workflow status later"\
}\
\\\

### 2. List Orders
**GET** \/orders\

Retrieves a paginated list of orders.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| \page\ | integer | 1 | Page number |
| \limit\ | integer | 10 | Items per page |

**Request:**
\\\ash
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders?page=1&limit=10"
\\\

**Response (200 OK):**
\\\json
{
  "orders": [
    {
      "order_id": "550e8400-e29b-41d4-a716-446655440000",
      "customer_id": "CUST001",
      "total_amount": 150.75,
      "status": "pending",
      "created_at": "2024-01-24T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
\\\

### 3. Get Order Details
**GET** \/orders/{order_id}\

Retrieves detailed information about a specific order including order items.

**Request:**
\\\ash
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders/550e8400-e29b-41d4-a716-446655440000"
\\\

**Response (200 OK):**
\\\json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "CUST001",
  "total_amount": 150.75,
  "status": "pending",
  "created_at": "2024-01-24T10:30:00",
  "items": [
    {
      "product_id": "PROD001",
      "quantity": 2,
      "price": 50.25
    },
    {
      "product_id": "PROD002",
      "quantity": 1,
      "price": 50.25
    }
  ]
}
\\\

### 4. Update Order Status
**PUT** \/orders/{order_id}\

Updates the status of an existing order.

**Request:**
\\\ash
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"status": "processing"}' \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders/550e8400-e29b-41d4-a716-446655440000"
\\\

**Response (200 OK):**
\\\json
{
  "message": "Order updated successfully",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
\\\

### 5. Delete Order
**DELETE** \/orders/{order_id}\

Deletes an order and its associated items from the database.

**Request:**
\\\ash
curl -X DELETE \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders/550e8400-e29b-41d4-a716-446655440000"
\\\

**Response (200 OK):**
\\\json
{
  "message": "Order deleted successfully",
  "order_id": "550e8400-e29b-41d4-a716-446655440000"
}
\\\

### 6. Get Workflow Status
**GET** \/status/{identifier}\

Checks the status of a Step Functions workflow execution. Accepts either execution ARN or order ID.

**Request with Order ID:**
\\\ash
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/status/550e8400-e29b-41d4-a716-446655440000"
\\\

**Request with Execution ARN:**
\\\ash
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/status/arn:aws:states:us-east-1:123456789012:execution:OrderProcessingStateMachine:550e8400-e29b-41d4-a716-446655440000"
\\\

**Response (200 OK):**
\\\json
{
  "execution_arn": "arn:aws:states:us-east-1:123456789012:execution:OrderProcessingStateMachine:550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING",
  "start_date": "2024-01-24T10:30:00",
  "input_identifier": "550e8400-e29b-41d4-a716-446655440000",
  "identifier_type": "order_id",
  "recent_events": [
    {
      "type": "ExecutionStarted",
      "timestamp": "2024-01-24T10:30:00",
      "state": null
    }
  ]
}
\\\

## Authentication

All endpoints require API Key authentication. Include the API Key in the request header:

\\\
x-api-key: your-api-key-here
\\\

## Database Schema

### Orders Table
\\\sql
CREATE TABLE orders (
    order_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE order_items (
    order_id VARCHAR(36) REFERENCES orders(order_id),
    product_id VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE inventory (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0
);
\\\

## Order Status Values

| Status | Description |
|--------|-------------|
| \pending\ | Order created, awaiting processing |
| \processing\ | Order is being processed |
| \shipped\ | Order has been shipped |
| \delivered\ | Order has been delivered |
| \cancelled\ | Order has been cancelled |
| \ailed\ | Order processing failed |

## Error Handling

### 400 Bad Request
\\\json
{
  "message": "Missing required field: customer_id"
}
\\\

### 403 Forbidden
\\\json
{
  "message": "Forbidden"
}
\\\

### 404 Not Found
\\\json
{
  "message": "Order not found"
}
\\\

### 500 Internal Server Error
\\\json
{
  "message": "Internal server error",
  "error": "Detailed error message"
}
\\\

## Testing

### Python Test Script

Create a file \	est_api.py\:

\\\python
import requests
import json

API_BASE_URL = "https://your-api-id.execute-api.region.amazonaws.com/stage"
API_KEY = "your-api-key-here"

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

def test_all_endpoints():
    print("=== Order Management API Test ===\n")
    
    # 1. Create Order
    print("1. Testing POST /orders")
    order_data = {
        "customer_id": "CUST001",
        "items": [
            {"product_id": "PROD001", "quantity": 2},
            {"product_id": "PROD002", "quantity": 1}
        ]
    }
    
    response = requests.post(f"{API_BASE_URL}/orders", 
                           headers=headers, 
                           json=order_data)
    
    if response.status_code == 201:
        order_response = response.json()
        order_id = order_response["order_id"]
        execution_arn = order_response["execution_arn"]
        
        print(f" Order created: {order_id}")
        print(f"  Execution ARN: {execution_arn}")
        
        # Test other endpoints...
        print("\n All tests completed successfully!")
        
    else:
        print(f" Failed to create order: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    test_all_endpoints()
\\\

### Bash Test Script

Create a file \	est_api.sh\:

\\\ash
#!/bin/bash

API_BASE="https://your-api-id.execute-api.region.amazonaws.com/stage"
API_KEY="your-api-key-here"

echo "=== Testing Order Management API ==="

# 1. Create Order
echo -e "\n1. Creating order..."
ORDER_RESPONSE=/orders

ORDER_ID=
EXECUTION_ARN=

echo "Order ID: "
echo "Execution ARN: "

# Continue with other tests...
echo -e "\n=== Test Complete ==="
\\\

## Setup & Deployment

### Prerequisites
1. AWS Account with appropriate permissions
2. RDS PostgreSQL database
3. S3 bucket for order backups
4. Step Functions state machine
5. API Gateway configured with API Key

### Environment Variables
Configure these environment variables in your Lambda function:

\\\ash
DB_HOST=your-rds-endpoint
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
S3_BUCKET=your-s3-bucket-name
STATE_MACHINE_ARN=arn:aws:states:region:account:stateMachine:OrderProcessingStateMachine
\\\

### IAM Permissions
The Lambda function requires permissions for:
- RDS database access
- S3 put object
- Step Functions start execution and describe execution
- CloudWatch Logs

## Sample Data

### Inventory Data
\\\sql
INSERT INTO inventory (product_id, product_name, price, stock) VALUES
('PROD001', 'Laptop', 999.99, 50),
('PROD002', 'Mouse', 29.99, 100),
('PROD003', 'Keyboard', 79.99, 75),
('PROD004', 'Monitor', 299.99, 30);
\\\

## Support

For issues and questions:
1. Check the error messages in the response
2. Verify API Key is valid and included in headers
3. Ensure database connection is configured correctly
4. Confirm Step Functions state machine exists and is accessible

## License

This project is licensed under the MIT License.
