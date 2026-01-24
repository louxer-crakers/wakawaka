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
\
{
  "message": "Order created successfully",\
  "order_id": "550e8400-e29b-41d4-a716-446655440000",\
  "execution_arn": "arn:aws:states:us-east-1:123456789012:execution:arnstepfunction",\
  "note": "Save this execution_arn to check workflow status later"\
}\
\

### 2. List Orders
**GET** \/orders

Retrieves a paginated list of orders.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| \page\ | integer | 1 | Page number |
| \limit\ | integer | 10 | Items per page |

**Request:**<br/>
\
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders?page=1&limit=10"
\

**Response (200 OK):**
\
{\
  "orders": [\
    {\
      "order_id": "550e8400-e29b-41d4-a716-446655440000",\
      "customer_id": "CUST001",\
      "total_amount": 150.75,\
      "status": "pending",\
      "created_at": "2024-01-24T10:30:00"\
    }\
  ],\
  "pagination": {\
    "page": 1,\
    "limit": 10,\
    "total": 25,\
    "pages": 3\
  }\
}\
\

### 3. Get Order Details
**GET** \/orders/{order_id}

Retrieves detailed information about a specific order including order items.\

**Request:**
\
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders/{id}"
\

**Response (200 OK):**
\
{\
  "order_id": "550e8400-e29b-41d4-a716-446655440000",\
  "customer_id": "CUST001",\
  "total_amount": 150.75,\
  "status": "pending",\
  "created_at": "2024-01-24T10:30:00",\
  "items": [\
    {\
      "product_id": "PROD001",\
      "quantity": 2,\
      "price": 50.25\
    },\
    {\
      "product_id": "PROD002",\
      "quantity": 1,\
      "price": 50.25\
    }\
  ]\
}

### 4. Update Order Status
**PUT** \/orders/{order_id}

Updates the status of an existing order.

**Request:**
\
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"status": "processing"}' \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders/550e8400-e29b-41d4-a716-446655440000"

**Response (200 OK):**
\
{
  "message": "Order updated successfully",\
  "order_id": "550e8400-e29b-41d4-a716-446655440000",\
  "status": "processing"\
}

### 5. Delete Order
**DELETE** \/orders/{order_id}

Deletes an order and its associated items from the database.

**Request:**
\
curl -X DELETE \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/orders/550e8400-e29b-41d4-a716-446655440000"

**Response (200 OK):**
\
{\
  "message": "Order deleted successfully",\
  "order_id": "550e8400-e29b-41d4-a716-446655440000"\
}

### 6. Get Workflow Status
**GET** \/status/{identifier}

Checks the status of a Step Functions workflow execution. Accepts either execution ARN or order ID.

**Request with Order ID:**
\
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/status/550e8400-e29b-41d4-a716-446655440000"

**Request with Execution ARN:**
\
curl -X GET \
  -H "x-api-key: YOUR_API_KEY" \
  "https://your-api-id.execute-api.region.amazonaws.com/stage/status/arn:aws:states:us-east-1:123456789012:execution:OrderProcessingStateMachine:550e8400-e29b-41d4-a716-446655440000"

**Response (200 OK):**
\
{\
  "execution_arn": "arn:aws:states:us-east-1:123456789012:execution:OrderProcessingStateMachine:550e8400-e29b-41d4-a716-446655440000",\
  "status": "RUNNING",\
  "start_date": "2024-01-24T10:30:00",\
  "input_identifier": "550e8400-e29b-41d4-a716-446655440000",\
  "identifier_type": "order_id",\
  "recent_events": [\
    {\
      "type": "ExecutionStarted",\
      "timestamp": "2024-01-24T10:30:00",\
      "state": null\
    }\
  ]\
}


## Authentication

All endpoints require API Key authentication. Include the API Key in the request header:

\
x-api-key: your-api-key-here


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
\
{\
  "message": "Missing required field: customer_id"\
}

### 403 Forbidden
\
{\
  "message": "Forbidden"\
}


### 404 Not Found
\
{\
  "message": "Order not found"\
}


### 500 Internal Server Error
\
{\
  "message": "Internal server error",\
  "error": "Detailed error message"\
}


## Support

For issues and questions:
1. Check the error messages in the response
2. Verify API Key is valid and included in headers
3. Ensure database connection is configured correctly
4. Confirm Step Functions state machine exists and is accessible

## License

This project is licensed under the MIT License.
