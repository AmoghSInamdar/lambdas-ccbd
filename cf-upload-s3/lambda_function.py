import json
import boto3
import base64

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    file, name = event['file'], event['name']
    obj = s3.Object('ai2442hw2photos', name)
    if event['x-amz-meta-customLabels']:
        res = obj.put(
            Body = base64.b64decode(file),
            Metadata = {'x-amz-meta-customLabels':event['x-amz-meta-customLabels']}
        )
    else:
        res = obj.put(Body = base64.b64decode(file))
    print(res)
    return {
        'statusCode': 200,
        'body': res
    }
