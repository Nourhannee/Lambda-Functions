import json
import boto3
from datetime import datetime, timezone, timedelta

# S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):

    bucket_name = "tts-service-storage-dev"   
    days_old = 30  
    now = datetime.now(timezone.utc)
    deleted_files = []

    response = s3.list_objects_v2(Bucket=bucket_name)

    if "Contents" not in response:
        return {
            'statusCode': 200,
            'body': json.dumps("Bucket is empty – no cleanup needed")
        }

    for obj in response["Contents"]:
        file_name = obj["Key"]
        last_modified = obj["LastModified"]

        age = now - last_modified

        if age > timedelta(days=days_old):
            s3.delete_object(Bucket=bucket_name, Key=file_name)
            deleted_files.append(file_name)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "message": "Cleanup completed",
            "bucket": bucket_name,
            "deleted_files": deleted_files
        })
    }
