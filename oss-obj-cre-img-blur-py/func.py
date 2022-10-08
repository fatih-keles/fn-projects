import io
import json
import logging
import oci
import uuid
import cv2
import os
import sys, traceback
import numpy as np


from fdk import response

local_test=False

# detected_faces = face_cascade.detectMultiScale(image=image, scaleFactor=1.3, minNeighbors=4)
# draw_found_faces(detected_faces, original_image, (0, 255, 0)) # RGB - green
def draw_found_faces(detected, image, color: tuple):
    for (x, y, width, height) in detected:
        cv2.rectangle(
            image,
            (x, y),
            (x + width, y + height),
            color,
            thickness=2
        )

def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """Return a sharpened version of the image, using an unsharp mask."""
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened

def edge_mask(image):
    """Return a edge masked version of the image"""
    kernel_edge = np.array([[-1, -1, -1],
                   [-1, 10,-1],
                   [-1, -1, -1]])
    edge_masked = cv2.filter2D(src=image, ddepth=-1, kernel=kernel_edge)
    return edge_masked

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
    image_original = cv2.imread(temp_file_input)
    image_processed = image_original
    
    # Grayscale image
    image_gray = cv2.cvtColor(image_processed, cv2.COLOR_BGR2GRAY)
    
    h, w = image_original.shape[:2]
    kernel_width = (w//30) | 1
    kernel_height = (h//30) | 1

    # face and license plate cascades 
    face_cascades = [
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml'),
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'),
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt_tree.xml'),
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml'),
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalcatface.xml'),
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'),
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_licence_plate_rus_16stages.xml')
    ]
    face_cascades_colors = [
        (255, 0, 0),(0, 255, 0),(0, 0, 255),(0, 0, 0),(255, 255, 255)
    ]

    logging.getLogger().debug("Face detection and blurring")
    i=0
    for face_cascade in face_cascades:
        faces = face_cascade.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=5)
        # print("{0} {1}".format(face_cascade, faces))
        for x, y, w, h in faces:
            #cv2.rectangle(image_processed, (x, y), (x+w, y+h), face_cascades_colors[i], 2);
            face_rectangle = image_processed[y:y+h, x:x+w]
            blurred_face = cv2.GaussianBlur(face_rectangle, (kernel_width, kernel_height), 0)
            image_processed[y:y+h, x:x+w] = blurred_face
        i=i+1

    # logging.getLogger().debug("Using config {}".format(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'))
    # face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    # #logging.getLogger().debug(face_cascade)
    # faces = face_cascade.detectMultiScale(image, 1.1, 5)
    # # logging.getLogger().debug("faces")
    # for x, y, w, h in faces:
    #     logging.getLogger().debug("Found a face and blurring")
    #     face_roi = image[y:y+h, x:x+w]
    #     # logging.getLogger().debug(face_roi)
    #     blurred_face = cv2.GaussianBlur(face_roi, (kernel_width, kernel_height), 0)
    #     # logging.getLogger().debug(blurred_face)
    #     image[y:y+h, x:x+w] = blurred_face

    temp_file_output="/tmp/"+uuid.uuid4().hex+"-"+object_name
    logging.getLogger().debug("Create temporary output file {}".format(temp_file_output))
    cv2.imwrite(temp_file_output,image_processed)

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
                {"status_code":"ERROR", "message": "{0}".format(stack_trace_string)}),
            headers={"Content-Type": "application/json"}
        )

    return response.Response(
        ctx, response_data=json.dumps(
            {"status_code":"SUCCESS", "message": "Successfuly processed image {0}".format(resourceName)}),
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
    # os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    # namespace=os_client.get_namespace().data
    # bucket_name="auto-blur-images"
    # object_name="us.jpeg"
    # logging.getLogger().debug("namespace: {}".format(namespace))

    # logging.getLogger().info("Get object {}".format(object_name))
    # os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    # resp = os_client.get_object(namespace_name=namespace, bucket_name=bucket_name, object_name=object_name)
    
    # temp_file_input="/tmp/"+uuid.uuid4().hex+"-"+object_name
    # logging.getLogger().debug("Create temporary input file {}".format(temp_file_input))
    # with open(temp_file_input, 'wb') as f:
    #     f.write(resp.data.content)
    
    logging.getLogger().debug("Process image")
    image = cv2.imread("sample-images/_advanced/seinfeld-1.jpg")
    # Convert to grayscale 
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Sharpen
    kernel = np.array([[0, -1, 0],
                   [-1, 5,-1],
                   [0, -1, 0]])
    # Edge
    kernel = np.array([[-1, -1, -1],
                   [-1, 16,-1],
                   [-1, -1, -1]])
    image = cv2.filter2D(src=image, ddepth=-1, kernel=kernel)

    h, w = image.shape[:2]
    kernel_width = (w//7) | 1
    kernel_height = (h//7) | 1

    logging.getLogger().debug("Face recognition and blurring")
    classifier_model=cv2.data.haarcascades + 'haarcascade_profileface.xml'
    logging.getLogger().debug("Using config {}".format(classifier_model))
    face_cascade = cv2.CascadeClassifier(classifier_model)
    # print(face_cascade)
    # faces = face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
    faces = face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
    print(faces)
    for x, y, w, h in faces:
        face_roi = image[y:y+h, x:x+w]
        # print(face_roi)
        blurred_face = cv2.GaussianBlur(face_roi, (kernel_width, kernel_height), 0)
        # print(blurred_face)
        image[y:y+h, x:x+w] = blurred_face

    # temp_file_output="/tmp/"+uuid.uuid4().hex+"-"+object_name
    temp_file_output='out.jpg'
    logging.getLogger().debug("Create temporary output file {}".format(temp_file_output))
    cv2.imwrite(temp_file_output,image)

    # with open(temp_file_output, "rb") as in_file:
    #     name = os.path.basename(temp_file_output)
    #     os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    #     resp = os_client.put_object(
    #         namespace_name=namespace,
    #         bucket_name=bucket_name,
    #         object_name=object_name,
    #         put_object_body=in_file
    #     )
    #     logging.getLogger().debug("Finished uploading {}".format(name))
    
    # logging.getLogger().debug("Removing temporariy files {0} {1}".format(temp_file_input, temp_file_output))
    # os.remove(temp_file_input)
    # os.remove(temp_file_output)

    try:
        logging.getLogger().info("Blur faces")
        x=1/0
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #formatted_lines = traceback.format_exc().splitlines()
        a=str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        logging.getLogger().error('Error: ' + str(ex))
        logging.getLogger().error('Trace: ' + a)
