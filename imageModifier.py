import json
import boto3
import cv2
import numpy as np
import io
import os
import base64
import time

def process_image(img, params):
    if params['type'] == 'bw':
        bw_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return bw_img
    elif params['type'] == 'resize':
        width = int(params['width'])
        height = int(params['height'])
        resized_img = cv2.resize(img, (width, height))
        return resized_img
    elif params['type'] == 'rotate':
        rotated_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        return rotated_img
    elif params['type'] == 'blur':
        blurred_img = cv2.GaussianBlur(img, (7, 7), 0)
        return blurred_img 
    elif params['type'] == 'sharpen':
        kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
        sharp_img = cv2.filter2D(img, -1, kernel)
        return sharp_img

def lambda_handler(event, context):
    """
    AWS Lambda function to process and modify images stored in our uploads S3 buckets.
    It retrieves an image from an S3 bucket based on event parameters,
    applies specified modifications to the image, and uploads the modified image back to the modified S3 bucket.
    The function returns the modified image encoded in base64 format.
    """
    s3 = boto3.client('s3')

    object_key = event['key']
    base_key, file_ext = os.path.splitext(object_key)
    modif_params = json.loads(event['modifications'])
    modif_count = int(modif_params['modif_count'])
    
    if modif_count > 0:
        bucket_name = 'new-cc-image-modified'
    else:
        bucket_name = 'new-cc-image-uploads'
        
    try:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=base_key
        )
        objects = response.get('Contents', [])
        print(objects)
        sorted_objects = sorted(objects, key=lambda obj: obj['Key'], reverse=True)
        most_recent_key = sorted_objects[0]['Key']

        s3_image_response = s3.get_object(Bucket=bucket_name, Key=most_recent_key)
        image_bytes = s3_image_response['Body'].read()
        img_array = np.frombuffer(image_bytes, np.uint8)
        decoded_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        processed_image = process_image(decoded_img, modif_params)

        file_ext = os.path.splitext(object_key)[1]
        success, encoded_image = cv2.imencode(file_ext, processed_image)
        if not success:
            raise Exception("Failed to encode image")
        processed_image_bytes = encoded_image.tobytes()

        metadata = { 'modif-params': json.dumps(modif_params) }
        bucket_name = 'new-cc-image-modified'
        timestamp = str(int(time.time()))
        new_key = f"{base_key}_{timestamp}{file_ext}"
        s3.put_object(
            Bucket=bucket_name,
            Key=new_key,
            Body=processed_image_bytes,
            ContentType="image/jpeg",
            Metadata=metadata
        )

        encode_img_body = base64.b64encode(processed_image_bytes).decode('utf-8')
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'image/jpeg'
            },
            'body': encode_img_body
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error modifying the image {base_key}: {str(e)}')
        }
