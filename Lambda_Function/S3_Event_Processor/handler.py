import json
import boto3
import os
import datetime
from kafka import KafkaProducer 

s3_client = boto3.client('s3')
KAFKA_TOPIC = "document.uploaded"
KAFKA_BROKERS = os.environ.get('KAFKA_BROKERS') 

try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKERS.split(','),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )
except Exception as e:
    print(f"ERROR: Kafka Producer initialization failed: {e}")
    producer = None


def lambda_handler(event, context):
    """
    Function triggered by S3 upload to read the file, extract metadata, and publish a Kafka event.
    """
    
    print("Received event: " + json.dumps(event))
    
    for record in event['Records']:
        if 's3' in record:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            print(f"Processing object: {object_key} from bucket: {bucket_name}")
            
            try:
                # 1. Get the object from S3
                file_object = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                
                # 2. Read content (Preview/Extraction)
                file_content_preview = file_object['Body'].read(500).decode('utf-8', errors='ignore')
                # *TODO: Add full document parsing logic here*

                # 3. Construct Kafka Payload
                kafka_payload = {
                    "document_id": object_key,
                    "s3_path": f"s3://{bucket_name}/{object_key}",
                    "user_id": "TODO_EXTRACT_USER_ID", # Placeholder for user ID
                    "preview": file_content_preview,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                
                # 4. Publish Event to Kafka
                if producer:
                    producer.send(KAFKA_TOPIC, kafka_payload)
                    producer.flush() 
                    print(f"Successfully published event for document ID: {object_key}")
                else:
                    print("WARN: Kafka Producer is not available. Skipping publish.")
                
            except Exception as e:
                print(f"ERROR: Processing failed for {object_key}: {e}")
                raise
                
    return {'status': 'OK', 'message': 'Document processing event initiated.'}


