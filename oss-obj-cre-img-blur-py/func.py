import io
import json
import logging
import oci
import uuid
import cv2
import os
import sys, traceback


from fdk import response

local_test=False

def blur_faces(signer, namespace, bucket_name, object_name):
    logging.getLogger().debug("Inside blur_faces - {}".format(1))
    logging.getLogger().debug("namespace: {}".format(namespace))
    logging.getLogger().debug("bucket_name: {}".format(bucket_name))
    logging.getLogger().debug("object_name: {}".format(object_name))

    logging.getLogger().info("Get object {}".format(object_name))
    os_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    resp = os_client.get_object(namespace_name=namespace, bucket_name=bucket_name, object_name=object_name)
    
    temp_file_input="/tmp/"+uuid.uuid4().hex+"-"+object_name    
    logging.getLogger().debug("Create temporary input file {}".format(temp_file_input))
    with open(temp_file_input, 'wb') as f:
        f.write(resp.data.content)
    
    logging.getLogger().debug("Process image")
    image = cv2.imread(temp_file_input)
    h, w = image.shape[:2]
    kernel_width = (w//7) | 1
    kernel_height = (h//7) | 1

    logging.getLogger().debug("Face recognition and blurring")
    #logging.getLogger().debug(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    #logging.getLogger().debug(face_cascade)
    faces = face_cascade.detectMultiScale(image, 1.1, 5)
    logging.getLogger().debug("faces")
    for x, y, w, h in faces:
        face_roi = image[y:y+h, x:x+w]
        logging.getLogger().debug(face_roi)
        blurred_face = cv2.GaussianBlur(face_roi, (kernel_width, kernel_height), 0)
        logging.getLogger().debug(blurred_face)
        image[y:y+h, x:x+w] = blurred_face

    temp_file_output="/tmp/"+uuid.uuid4().hex+"-"+object_name
    logging.getLogger().debug("Create temporary output file {}".format(temp_file_output))
    cv2.imwrite(temp_file_output,image)

    with open(temp_file_output, "rb") as in_file:
        name = os.path.basename(temp_file_output)
        os_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        resp = os_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name,
            put_object_body=in_file
        )
        logging.getLogger().debug("Finished uploading {}".format(name))
    
    logging.getLogger().debug("Removing temporary files {0} {1}".format(temp_file_input, temp_file_output))
    os.remove(temp_file_input)
    os.remove(temp_file_output)


def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().debug("Inside Python handler")
    signer = oci.auth.signers.get_resource_principals_signer()
    config = ctx.Config()
    eventID = eventTime = compartmentId = compartmentName = resourceName = resourceId = namespace = bucketName = bucketId = ""
    return_code = return_message = ""

    ## Get Config
    try:
        ## ERROR = 40
        ## INFO = 20
        ## DEBUG = 10
        s_log_level = config["log-level"]
        log_level = 40
        if s_log_level == "ERROR":
            log_level = 40
        if s_log_level == "INFO":
            log_level = 20
        if s_log_level == "DEBUG":
            log_level = 10
        logging.getLogger().setLevel(log_level)
    except Exception as ex:
        logging.getLogger().error('Missing function config parameters: ' + str(ex))
        raise

    try:
        body = json.loads(data.getvalue())

        eventID=body["eventID"]
        eventTime=body["eventTime"]
        compartmentId=body["data"]["compartmentId"]
        compartmentName=body["data"]["compartmentName"]
        resourceName=body["data"]["resourceName"]
        resourceId=body["data"]["resourceId"]
        namespace=body["data"]["additionalDetails"]["namespace"]
        bucketName=body["data"]["additionalDetails"]["bucketName"]
        bucketId= body["data"]["additionalDetails"]["bucketId"]
        #
        logging.getLogger().debug("eventID : {}".format(eventID))
        logging.getLogger().debug("eventTime : {}".format(eventTime))
        logging.getLogger().debug("compartmentId : {}".format(compartmentId))
        logging.getLogger().debug("compartmentName : {}".format(compartmentName))
        logging.getLogger().debug("resourceId : {}".format(resourceId))
        logging.getLogger().debug("resourceName : {}".format(resourceName))
        logging.getLogger().debug("namespace : {}".format(namespace))
        logging.getLogger().debug("bucketName : {}".format(bucketName))
        logging.getLogger().debug("bucketId : {}".format(bucketId))
    except (Exception, ValueError) as ex:
        logging.getLogger().error('error parsing json payload: ' + str(ex))
        raise
    
    try:
        logging.getLogger().info("Blur faces")
        blur_faces(signer, namespace, bucket_name=bucketName, object_name=resourceName)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #formatted_lines = traceback.format_exc().splitlines()
        logging.getLogger().error('Error: ' + str(ex))
        stack_trace_string = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        logging.getLogger().error('Trace: ' + stack_trace_string)
        return response.Response(
            ctx, response_data=json.dumps(
                {"message": "{0}".format(stack_trace_string)}),
            headers={"Content-Type": "application/json"}
        )

    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Successfuly processed image {0}".format(resourceName)}),
        headers={"Content-Type": "application/json"}
    )

if local_test:
    config = oci.config.from_file("~/.oci/config","DEFAULT")
    identity = oci.identity.IdentityClient(config)
    user = identity.get_user(config["user"]).data
    signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
    os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    namespace=os_client.get_namespace().data
    bucket_name="auto-blur-images"
    object_name="us.jpeg"
    logging.getLogger().debug("namespace: {}".format(namespace))

    logging.getLogger().info("Get object {}".format(object_name))
    os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    resp = os_client.get_object(namespace_name=namespace, bucket_name=bucket_name, object_name=object_name)
    
    temp_file_input="/tmp/"+uuid.uuid4().hex+"-"+object_name
    logging.getLogger().debug("Create temporary input file {}".format(temp_file_input))
    with open(temp_file_input, 'wb') as f:
        f.write(resp.data.content)
    
    logging.getLogger().debug("Process image")
    image = cv2.imread(temp_file_input)
    h, w = image.shape[:2]
    kernel_width = (w//7) | 1
    kernel_height = (h//7) | 1

    logging.getLogger().debug("Face recognition and blurring")
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    print(face_cascade)
    faces = face_cascade.detectMultiScale(image, 1.1, 5)
    print(faces)
    for x, y, w, h in faces:
        face_roi = image[y:y+h, x:x+w]
        print(face_roi)
        blurred_face = cv2.GaussianBlur(face_roi, (kernel_width, kernel_height), 0)
        print(blurred_face)
        image[y:y+h, x:x+w] = blurred_face

    temp_file_output="/tmp/"+uuid.uuid4().hex+"-"+object_name
    logging.getLogger().debug("Create temporary output file {}".format(temp_file_output))
    cv2.imwrite(temp_file_output,image)

    with open(temp_file_output, "rb") as in_file:
        name = os.path.basename(temp_file_output)
        os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
        resp = os_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name,
            put_object_body=in_file
        )
        logging.getLogger().debug("Finished uploading {}".format(name))
    
    logging.getLogger().debug("Removing temporariy files {0} {1}".format(temp_file_input, temp_file_output))
    os.remove(temp_file_input)
    os.remove(temp_file_output)

    try:
        logging.getLogger().info("Blur faces")
        x=1/0
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #formatted_lines = traceback.format_exc().splitlines()
        a=str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        logging.getLogger().error('Error: ' + str(ex))
        logging.getLogger().error('Trace: ' + a)
