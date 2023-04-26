import json
import os
import time
import urllib.parse

from contextlib import contextmanager
from io import BytesIO

import boto3
import pandas as pd

print('Loading function')

@contextmanager
def timer(name, log_time):
    start_time = time.time()
    try:
        yield
    finally:
        if log_time:
            print(f'{name} took {time.time()-start_time:.3f}s')


DESTINATION_BUCKET = os.environ.get('DESTINATION_BUCKET', 'sst-output') # S3
DESTINATION_TABLE = os.environ.get('DESTINATION_BUCKET', 'sst-outputs') # DynamoDB

INDEX_COLUMN = 'PassengerId'

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')


def extract(bucket_name, key):
    print(f'trying to load {key} from {bucket_name}')
    bucket = s3.Bucket(bucket_name)
    s3_object = bucket.Object(key).get()
    # s3_object = s3.get_object(Bucket=bucket_name, Key=key)
    s3_bytes = s3_object['Body'].read()
    return pd.read_csv(BytesIO(s3_bytes), index_col=INDEX_COLUMN)


def transform(df):
    # creating more informative data from raw compund values
    print('transforming data')
    df[['CabinDeck', 'CabinNum', 'CabinSide']] = df.Cabin.str.split('/', expand=True)
    df['GroupId'] = df.index.str.split('_', expand=True).get_level_values(0).astype('int32')
    df['FamilyName'] = df.Name.str.split(' ', expand=True)[1]
    return df


def load_s3(df, file_name, destination_bucket=DESTINATION_BUCKET):
    df_bytes = BytesIO()
    df.to_csv(df_bytes, index_label=INDEX_COLUMN)
    df_bytes.seek(0)
    print('trying to write to S3', destination_bucket)
    bucket = s3.Bucket(destination_bucket)
    bucket.upload_fileobj(df_bytes, file_name)
    # s3.upload_fileobj(df_bytes, destination_bucket, file_name)


def load_dynamodb(df, file_name, destination_table=DESTINATION_TABLE):
    # note: just to try it out; writing so many records is actually too expensive
    # using filename as partition key in table
    df['filename'] = file_name
    # need to convert floats to strings
    records = df.reset_index().astype(str).to_dict(orient='records')

    table = dynamodb.Table(destination_table)
    print(f'trying to write {len(records)} records to DynamoDB table {destination_table}')
    with table.batch_writer() as batch:
        for record in records:
            batch.put_item(record)
    # table.put_item(Item={'id': file_name, 'data': json_object})


def lambda_handler(event, context, log_time=True):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    s3_data = event['Records'][0]['s3']
    bucket_name = s3_data['bucket']['name']
    key = urllib.parse.unquote_plus(s3_data['object']['key'], encoding='utf-8')
    try:
        with timer('extracting', log_time):
            df = extract(bucket_name, key)
        # print(df.head())
        with timer('transforming', log_time):
            transformed = transform(df)
        # write the result
        with timer('loading to S3', log_time):
            load_s3(transformed, key)
        # load_dynamodb(transformed, key)
        return True
    except Exception as e:
        print(e)
        print(f'Error getting object {key} from bucket {bucket_name}. Make sure they exist and your '
               'bucket is in the same region as this function.')
        raise e
