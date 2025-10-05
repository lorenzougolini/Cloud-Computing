import json
import boto3
import os

BUCKET_MODIFIED = 'new-cc-image-modified'
BUCKET_UPLOADS = 'new-cc-image-uploads'

s3 = boto3.client('s3')


def lambda_handler(event, context):
    """
    Handles a DELETE request from API Gateway. Finds all objects in our S3 buckets
    with a given prefix and deletes them.
    The image name is passed as a query string parameter named 'key'.
    """
    try:
        object_key = event['queryStringParameters']['key']
        prefix, file_ext = os.path.splitext(object_key)
        if not prefix:
            raise ValueError("The 'key' parameter cannot be empty.")
    except (KeyError, TypeError):
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': "Missing required 'key' query string parameter."})
        }
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

    try:
        # delete from modified
        objects_to_delete = []
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET_MODIFIED, Prefix=prefix)

        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})

        total_deleted = 0
        if len(objects_to_delete)>0:
            for i in range(0, len(objects_to_delete), 1000):
                chunk = objects_to_delete[i:i + 1000]
                response = s3.delete_objects(
                    Bucket=BUCKET_MODIFIED,
                    Delete={'Objects': chunk, 'Quiet': True}
                )
                total_deleted += len(chunk)

                if 'Errors' in response:
                    raise Exception("Failed to delete some objects.")
        
        # delete from uploads
        s3.delete_object(Bucket=BUCKET_UPLOADS, Key=object_key)
        total_deleted += 1

        success_message = f"Successfully deleted {total_deleted} object(s) with prefix '{prefix}'."
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': 'http://new-cc-website-host.s3-website-us-east-1.amazonaws.com'
            },
            'body': json.dumps({'message': success_message})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'An internal server error occurred: {str(e)}'})
        }