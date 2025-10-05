import json
import base64
import boto3
from io import BytesIO
import uuid
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    AWS Lambda function to handle image uploads to the uploads S3 bucket.
    It receives an event containing a base64-encoded image, its key(name), type, and modification count.
    If the image has already been uploaded (modif_count != 0), it returns a 204.
    Otherwise, it decodes the image, generates a unique object key, and uploads the image to the uploads S3 bucket.
    """
    try:
        base64_image = event['image']
        object_key = event['key']
        object_type = event['type']

        if event['modif_count'] != 0:
            return {
                'statusCode': 204,
                    'body': json.dumps({
                    'message': 'Image already uploaded',
                    'object_key_id': object_key
                })
            }

        image_data = base64.b64decode(base64_image)
        
        bucket_name = 'new-cc-image-uploads'
        base_key, file_ext = os.path.splitext(object_key)
        object_key_id = str(uuid.uuid4())+file_ext
        s3.put_object(
            Bucket=bucket_name,
            Key=object_key_id,
            Body=image_data,
            ContentType=object_type,
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image uploaded successfully to S3',
                'object_key_id': object_key_id
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error uploading the image: {str(e)}')
        }
