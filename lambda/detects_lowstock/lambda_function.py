import json
import os
import psycopg2
import boto3
from datetime import datetime

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
    print(f"=== CUSTOM LAMBDA FUNCTION STARTS ===")

    

    print(f"Event received: {json.dumps(event, indent=2)}")