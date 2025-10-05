import json
import boto3
import base64
import os

s3 = boto3.client('s3')

MODIFIED_BUCKET = 'new-cc-image-modified'
UPLOADS_BUCKET = 'new-cc-image-uploads'

def lambda_handler(event, context):
    """
    Finds all versions of an image, deletes the most recent, and returns
    the second most recent. If only one exists, it is deleted and the
    original is returned.
    """
    try:
        key = event.get("queryStringParameters", {}).get("key")
        base_key, file_ext = os.path.splitext(key)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal Server Error: {str(e)}, {event}')
        }

    try:
        objects = s3.list_objects_v2(
            Bucket=MODIFIED_BUCKET,
            Prefix=base_key
        )

        modified_objects = objects.get('Contents', [])

        if not modified_objects:
            return {
                'statusCode': 404,
                'body': json.dumps(f'No modified images found for key: {base_key}')
            }

        sorted_objects = sorted(modified_objects, key=lambda obj: obj['Key'], reverse=True)
        
        bucket_to_get_from = ""
        key_to_return = ""

        if len(sorted_objects) >= 2:
            most_recent_key = sorted_objects[0]['Key']
            second_most_recent_key = sorted_objects[1]['Key']

            s3.delete_object(Bucket=MODIFIED_BUCKET, Key=most_recent_key)
            
            key_to_return = second_most_recent_key
            bucket_to_get_from = MODIFIED_BUCKET

        elif len(sorted_objects) == 1:
            only_object_key = sorted_objects[0]['Key']
            
            s3.delete_object(Bucket=MODIFIED_BUCKET, Key=only_object_key)
            
            key_to_return = base_key+file_ext
            bucket_to_get_from = UPLOADS_BUCKET
        
        image_object = s3.get_object(Bucket=bucket_to_get_from, Key=key_to_return)
        image_bytes = image_object['Body'].read()
        
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'image/jpeg',
                'Access-Control-Allow-Origin': 'http://new-cc-website-host.s3-website-us-east-1.amazonaws.com'
            },
            'body': encoded_image
        }
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal Server Error: {str(e)}, {second_most_recent_key}')
        }
