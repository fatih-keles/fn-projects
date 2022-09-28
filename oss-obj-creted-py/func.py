import io
import json
import oci
import logging
import requests
import uuid
import hashlib

from fdk import response

def persist_data(api_url, json_data, headers):
    #response = requests.post(api_url, data=json.dumps(json_data), headers=headers)
    requests.put(api_url.join(json_data.resource_id_hash), data=json.dumps(json_data), headers=headers)
    status_code = response.status_code
    logging.getLogger().info("Response.StatusCode: {0} ".format(status_code))
    if status_code not in [200, 201]: ##200: Updated, 201: Created
        raise Exception("Cannot persist object {0} on bucket {1}".format(json_data.resource_name, json_data.bucket_name))
"""
    if status_code == 400:
        resource_id_hash = json_data.resource_id_hash
        logging.getLogger().info("## Hit an existing row, update it with new values using primary key {}".format(resource_id_hash))
        requests.put(api_url.join(resource_id_hash), data=json.dumps(json_data), headers=headers)
        status_code = response.status_code
"""

def analyze_document_online(config, signer, namespace, bucket_name, object_name):
    ai_vision_client = oci.ai_vision.AIServiceVisionClient(config=config, signer=signer)
    resp = ai_vision_client.analyze_document(
        analyze_document_details=oci.ai_vision.models.AnalyzeDocumentDetails(
            features=[
                oci.ai_vision.models.DocumentFeature(feature_type=oci.ai_vision.models.DocumentFeature.FEATURE_TYPE_DOCUMENT_CLASSIFICATION),
                oci.ai_vision.models.DocumentFeature(feature_type=oci.ai_vision.models.DocumentFeature.FEATURE_TYPE_LANGUAGE_CLASSIFICATION),
                oci.ai_vision.models.DocumentFeature(feature_type=oci.ai_vision.models.DocumentFeature.FEATURE_TYPE_TEXT_DETECTION)
            ],
            document=oci.ai_vision.models.ObjectStorageDocumentDetails(
                source="OBJECT_STORAGE", 
                namespace_name=namespace,
                bucket_name=bucket_name,
                object_name=object_name
            )
        ),
        opc_request_id=uuid.uuid4().hex
    )

    print(resp.status)
    print(resp.request_id)
    #with open('out.txt', 'w', encoding='utf-8') as f:
    #    f.write(str(resp.data))
    #print(resp.data)

    if resp.status != 200:
        raise Exception("Cannot analyze object {0} on bucket {1}".format(object_name, bucket_name))
    else:
        logging.getLogger().info("Object {0} bucket {1} analyzed".format(object_name, bucket_name))
        document_type=resp.data.detected_document_types[0].document_type
        language_code=resp.data.detected_languages[0].language_code
        page_count=resp.data.document_metadata.page_count
        logging.getLogger().info("document_type:{0}".format(document_type))
        logging.getLogger().info("language_code:{0}".format(language_code))
        extracted_text = ""
        for page in resp.data.pages:
            for line in page.lines:
                #print(" {0} ".format(line.text))
                extracted_text=extracted_text.join([line.text, " "]) 
        print("extracted_text:{0}".format(extracted_text))
        ##
        return {"document_type":document_type, "language_code":language_code,"page_count":page_count, "extracted_text":extracted_text}

def move_object(signer, namespace, source_bucket, destination_bucket, object_name):
    objstore = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    objstore_composite_ops = oci.object_storage.ObjectStorageClientCompositeOperations(objstore)
    resp = objstore_composite_ops.copy_object_and_wait_for_state(
        namespace,
        source_bucket,
        oci.object_storage.models.CopyObjectDetails(
            destination_bucket=destination_bucket,
            destination_namespace=namespace,
            destination_object_name=object_name,
            destination_region=signer.region,
            source_object_name=object_name
        ),
        wait_for_states=[
            oci.object_storage.models.WorkRequest.STATUS_COMPLETED,
            oci.object_storage.models.WorkRequest.STATUS_FAILED])
    if resp.data.status != "COMPLETED":
        raise Exception("cannot copy object {0} to bucket {1}".format(object_name, destination_bucket))
    else:
        resp = objstore.delete_object(namespace, source_bucket, object_name)
        logging.getLogger().info("Object {0} moved to Bucket {1}".format(object_name, destination_bucket))

def handler(ctx, data: io.BytesIO = None):
    signer = oci.auth.signers.get_resource_principals_signer()
    config = ctx.Config()
    eventID = eventTime = compartmentId = compartmentName = resourceName = resourceId = namespace = bucketName = bucketId = ""
    try:
        body = json.loads(data.getvalue())
        #print("INFO - Event ID {} received".format(body["eventID"]), flush=True)
        #print("INFO - Object name: " + body["data"]["resourceName"], flush=True)
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
        logging.getLogger().info("eventID : {}".format(eventID))
        logging.getLogger().info("eventTime : {}".format(eventTime))
        logging.getLogger().info("compartmentId : {}".format(compartmentId))
        logging.getLogger().info("compartmentName : {}".format(compartmentName))
        logging.getLogger().info("resourceId : {}".format(resourceId))
        logging.getLogger().info("resourceName : {}".format(resourceName))
        logging.getLogger().info("namespace : {}".format(namespace))
        logging.getLogger().info("bucketName : {}".format(bucketName))
        logging.getLogger().info("bucketId : {}".format(bucketId))
    except (Exception, ValueError) as ex:
        logging.getLogger().error('error parsing json payload: ' + str(ex))
        raise

    logging.getLogger().info("Analyzing objects")
    ai_result = analyze_document_online(config=config, signer=signer, namespace=namespace, bucket_name=bucketName, object_name=resourceName)

    logging.getLogger().info("inserting data")
    api_url = "https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"
    json_data = {
        "resource_id_hash": hashlib.md5(resourceId.encode('utf-8')).hexdigest(),
        "resource_id": resourceId,
        "event_id": eventID,
        "event_time": eventTime,
        "compartment_id": compartmentId,
        "compartment_name": compartmentName,
        "resource_name": resourceName,
        "os_namespace": namespace,
        "bucket_name": bucketName,
        "bucket_id": bucketId,
        "extracted_text": ai_result["extracted_text"],
        "document_type":ai_result["document_type"],
        "language_code":ai_result["language_code"],
        "page_count":ai_result["page_count"]
        }
    headers =  {"Content-Type":"application/json"}
    persist_data(api_url, json_data, headers)

    logging.getLogger().info("Moving objects")
    processed_bucket = "document_processed"
    #move_object(signer, namespace=namespace, source_bucket=bucketName, destination_bucket=processed_bucket, object_name=resourceName)

    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(resourceName)}),
        headers={"Content-Type": "application/json"}
    )

