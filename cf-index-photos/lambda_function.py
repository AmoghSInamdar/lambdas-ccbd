import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

host = 'search-photo-rsb5f3jtemgu7ygrulujhzwdgi.us-east-1.es.amazonaws.com'
region = 'us-east-1'

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)


def index_images(event, tags):
    for i in range(len(tags)):
        record = event['Records'][i]
        document = {
            'bucket': record['s3']['bucket']['name'],
            'name': record['s3']['object']['key'],
            'tags': tags[i]
        }
        es.index(index='photos', doc_type='_doc', body=document)


rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

def get_labels(event):
    tags = []
    for record in event['Records']:
        res = rekognition.detect_labels(Image={
            'S3Object': {
                'Bucket': record['s3']['bucket']['name'],
                'Name': record['s3']['object']['key']
            }
        })
        t = []
        for lab in res['Labels']:
            t.append(lab['Name'])
        tags.append(t)
        
    for r in range(len(event['Records'])):
        record = event['Records'][r]
        head = s3.head_object(
                Bucket = record['s3']['bucket']['name'],
                Key = record['s3']['object']['key']
            )
        if 'x-amz-meta-customlabels' in head['Metadata']:
            labels = head['Metadata']['x-amz-meta-customlabels']
            print(labels)
            if type(labels) == list:
                tags[r].extend(labels)
            else:
                tags[r].append(labels)
        print(head)
    return tags
    
def lambda_handler(event, context):
    tags = get_labels(event)
    index_images(event, tags)
    return {
        'statusCode': 200,
        'tags': tags
    }

