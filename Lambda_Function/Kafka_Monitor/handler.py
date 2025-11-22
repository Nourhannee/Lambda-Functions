import json
import boto3
from kafka import KafkaConsumer, TopicPartition
from datetime import datetime, timezone
import os

cw = boto3.client("cloudwatch")

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP")
TOPICS = os.getenv("TOPICS").split(",")  # Support multiple topics
GROUP_ID = os.getenv("GROUP_ID", None)
CLOUDWATCH_NAMESPACE = os.getenv("CLOUDWATCH_NAMESPACE", "KafkaMonitor")
METRIC_NAME = os.getenv("METRIC_NAME", "TopicLag")

def put_metric(value, topic_name):
    cw.put_metric_data(
        Namespace=CLOUDWATCH_NAMESPACE,
        MetricData=[{
            'MetricName': METRIC_NAME,
            'Dimensions': [{'Name':'Topic','Value': topic_name}],
            'Timestamp': datetime.now(timezone.utc),
            'Value': float(value),
            'Unit': 'Count'
        }]
    )

def lambda_handler(event, context):
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            enable_auto_commit=False,
            consumer_timeout_ms=10000
        )

        for topic in TOPICS:
            partitions = consumer.partitions_for_topic(topic)
            if not partitions:
                print(f"No partitions found for topic {topic}")
                continue

            topic_lag = 0
            for p in partitions:
                tp = TopicPartition(topic, p)
                consumer.assign([tp])
                consumer.seek_to_end(tp)
                end = consumer.position(tp)
                consumer.seek_to_beginning(tp)
                begin = consumer.position(tp)
                lag = max(0, end - begin)
                topic_lag += lag

            put_metric(topic_lag, topic)
            print(f"Topic: {topic}, lag: {topic_lag}")

        consumer.close()
        return {"statusCode": 200, "body": json.dumps("Kafka monitor completed")}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps(str(e))}
