import io
import json
import oci
import logging

from fdk import response


def analyze_document(signer, namespace, bucket_name, object_name):
    # oci ai-vision analyze-document --document file://analyze-document/document.json --features file://analyze-document/features.json
    ai_vision = oci.ai_vision.AIServiceVisionClientCompositeOperations(config={}, signer=signer)
    resp = ai_vision.create_document_job_and_wait_for_state(
        create_document_job_details=oci.ai_vision.models.CreateDocumentJobDetails(
            input_location=oci.ai_vision.models.InputLocation(
                source_type='OBJECT_STORAGE',
                object_locations=[oci.ai_vision.models.ObjectLocation(
                    namespace_name=namespace,
                    bucket_name=bucket_name,
                    object_name=object_name
                )]),
            features=[oci.ai_vision.models.DocumentFeature(
                featureType='DOCUMENT_CLASSIFICATION',
                maxResults=5
            )]
        ),
        wait_for_states=[
            oci.object_storage.models.WorkRequest.STATUS_COMPLETED,
            oci.object_storage.models.WorkRequest.STATUS_FAILED])
    
    logging.getLogger().info("{0}".format(json.dumps(resp, indent=4)))
    if resp.data.status != "COMPLETED":
        raise Exception("cannot anlayze object {0} on bucket {1}".format(object_name, bucket_name))
    else:
        logging.getLogger().info("Object {0} bucket {1} anlayzed".format(object_name, bucket_name))

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
    namespace = bucket_name = object_name = ordsbaseurl = schema = dbuser = dbpwd = ""
    try:
        body = json.loads(data.getvalue())
        # print("INFO - Event ID {} received".format(body["eventID"]), flush=True)
        # print("INFO - Object name: " + body["data"]["resourceName"], flush=True)
        namespace = body["data"]["additionalDetails"]["namespace"]
        bucket_name = body["data"]["additionalDetails"]["bucketName"]
        object_name = body["data"]["resourceName"]

        logging.getLogger().info("namespace : {}".format(namespace))
        logging.getLogger().info("bucketName : {}".format(bucket_name))
        logging.getLogger().info("resourceName : {}".format(object_name))
    except (Exception, ValueError) as ex:
        logging.getLogger().error('error parsing json payload: ' + str(ex))
        raise

    logging.getLogger().info("Analyzing objects")
    analyze_document(signer, namespace, bucket_name, object_name)

    logging.getLogger().info("Moving objects")
    input_bucket = bucket_name
    processed_bucket = "document_processed"
    move_object(signer, namespace, input_bucket, processed_bucket, object_name)

    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(object_name)}),
        headers={"Content-Type": "application/json"}
    )
