import io
import json
import oci
import logging

from fdk import response

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
        raise Exception("cannot copy object {0} to bucket {1}".format(object_name,destination_bucket))
    else:
        resp = objstore.delete_object(namespace, source_bucket, object_name)
        logging.getLogger().info("Object {0} moved to Bucket {1}".format(object_name,destination_bucket))


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

    logging.getLogger().info("Moving objects")
    input_bucket = bucket_name
    processed_bucket = "document_processed"
    move_object(signer, namespace, input_bucket, processed_bucket, object_name)

    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(object_name)}),
        headers={"Content-Type": "application/json"}
    )
