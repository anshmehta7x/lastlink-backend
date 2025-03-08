import boto3
from app.config import AWS_SECRET_KEY, AWS_ACCESS_KEY, AWS_REGION, AWS_TABLE_NAME

def initialize_connection():
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    users_table = dynamodb.Table(AWS_TABLE_NAME)
    return users_table
