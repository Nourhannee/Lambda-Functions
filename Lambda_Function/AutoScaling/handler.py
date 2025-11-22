import boto3
import os

cloudwatch = boto3.client('cloudwatch')
autoscaling = boto3.client('application-autoscaling')

# Config
SERVICE_NAMESPACE = 'ecs'
RESOURCE_ID = 'service/cluster-name/service-name'
SCALING_POLICY_NAME = 'MyScalingPolicy'
METRIC_NAME = 'CPUUtilization'
THRESHOLD_UP = 70
THRESHOLD_DOWN = 30

def lambda_handler(event, context):
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ECS',
                        'MetricName': METRIC_NAME,
                        'Dimensions': [{'Name':'ServiceName','Value':'service-name'}]
                    },
                    'Period': 300,
                    'Stat': 'Average'
                }
            }
        ],
        StartTime=datetime.utcnow()-timedelta(minutes=10),
        EndTime=datetime.utcnow()
    )

    avg_cpu = response['MetricDataResults'][0]['Values'][-1]

    if avg_cpu > THRESHOLD_UP:
        autoscaling.register_scalable_target(
            ServiceNamespace=SERVICE_NAMESPACE,
            ResourceId=RESOURCE_ID,
            ScalableDimension='ecs:service:DesiredCount',
            MinCapacity=1,
            MaxCapacity=10
        )
        print("Scaling up triggered!")
    elif avg_cpu < THRESHOLD_DOWN:
        print("Scaling down triggered!")

    return {"statusCode":200,"body":"Scaling check completed"}

