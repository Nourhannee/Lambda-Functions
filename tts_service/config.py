import os

# S3
TTS_BUCKET = os.environ.get('TTS_BUCKET', 'tts-service-storage-dev-bucket')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Redis (اختياري)
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_TTL = int(os.environ.get('REDIS_TTL', 3600))  # cache expiry in seconds
