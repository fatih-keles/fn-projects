import io
import json
import logging
import oci

from fdk import response

local_test=True

def get_object(signer, namespace, bucket_name, object_name):
    os_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    resp = os_client.get_object(namespace_name=namespace, bucket_name=bucket_name, object_name=object_name)


def handler(ctx, data: io.BytesIO = None):
    signer = oci.auth.signers.get_resource_principals_signer()
    config = ctx.Config()
    eventID = eventTime = compartmentId = compartmentName = resourceName = resourceId = namespace = bucketName = bucketId = ""
    
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
    except Exception as e:
        logging.getLogger().error('Missing function config parameters: ' + str(ex))
        raise

    name = "World"
    try:
        body = json.loads(data.getvalue())
        name = body.get("name")

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

    logging.getLogger().info("Inside Python Hello World function")
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(name)}),
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
    logging.getLogger().info("namespace: {}".format(namespace))

    os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    resp = os_client.get_object(namespace_name=namespace, bucket_name=bucket_name, object_name=object_name)
    with open('download.jpeg', 'wb') as f:
        f.write(resp.data.content)
    print(resp.data)

