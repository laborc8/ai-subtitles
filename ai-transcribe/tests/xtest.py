import boto3
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

session = boto3.session.Session()
credentials = session.get_credentials()
#print("Access Key:", credentials.access_key)
#print("Secret Key:", credentials.secret_key)

s3 = boto3.client('s3')
print(s3.list_buckets())
