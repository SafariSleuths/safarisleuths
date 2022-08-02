import os

import boto3

S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', None)
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', None)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', None)

s3 = None
s3_bucket = None

if None not in [S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME]:
    s3 = boto3.resource('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
    s3_bucket = s3.Bucket(S3_BUCKET_NAME)
