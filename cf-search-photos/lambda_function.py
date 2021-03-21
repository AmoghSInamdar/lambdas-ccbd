import json
import random
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

def search_es(tags):
    headers = { "Content-Type": "application/json" }
    q = { 
        "size": 20,
        "query": {
            "query_string": {
                "default_field": "tags",
                "query": None
            }
        }
    }
    results = []
    for tag in tags:
        print(tag)
        if tag[-1] == 's':
            tag = tag[:-1]
        q['query']['query_string']['query'] = tag 
        r = es.search(index='photos', doc_type='_doc', body=q)
        results.append(r)
        print(r)
    out = []
    for res in results:
        for hit in res['hits']['hits']:
            out.append({
                'bucket': hit['_source']['bucket'],
                'key': hit['_source']['name']
            })
    return out

lex = boto3.client('lex-runtime')

def get_lex_tags(input):
    response = lex.post_text(
        botName = 'photos',
        botAlias = 'photo',
        userId = 'default',
        inputText = input,
    )
    if 'slots' in response:
        tags = []
        for val in response['slots'].values():
            if type(val) == str:
                tags.append(val)
        return tags
    return None


def lambda_handler(event, context):
    tags = get_lex_tags(event['params']['querystring']['q'])
    res = search_es(tags) if tags is not None else []
    urls = []
    keys = set()
    for r in res:
        if r['key'] not in keys:
            keys.add(r['key'])
            urls.append('https://ai2442hw2photos.s3.amazonaws.com/'+r['key'])
    return {
        'statusCode': 200,
        'tags': tags,
        'res': res,
        'urls': urls
    }
    
