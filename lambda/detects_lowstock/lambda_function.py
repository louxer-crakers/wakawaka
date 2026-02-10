import json
import os
import psycopg2
import boto3
from datetime import datetime

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

sns_client = boto3.client("sns")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def lambda_handler(event, context):
    print(f"=== CUSTOM LAMBDA FUNCTION STARTS ===")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
            SELECT stock_quantity, product_name
            FROM inventory
            WHERE stock_quantity <= 10
        """)

    result = cur.fetchall()
    
    if not result:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Low Stock Detected",
            Message=result
        )
    continue

    return {
            "status": "stock detection finished",
    }