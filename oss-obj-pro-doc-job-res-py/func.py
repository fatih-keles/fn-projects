import io
import json
import logging
import oci
import hashlib
import requests

from fdk import response

def delete_object(signer, namespace, bucket_name, object_name):
    objstore = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    resp = objstore.delete_object(namespace, bucket_name, object_name)
    logging.getLogger().info("Object {0} deleted ".format(object_name))

def move_object(signer, namespace, source_bucket, destination_bucket, source_object_name, destination_object_name):
    objstore = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    objstore_composite_ops = oci.object_storage.ObjectStorageClientCompositeOperations(objstore)
    resp = objstore_composite_ops.copy_object_and_wait_for_state(
        namespace,
        source_bucket,
        oci.object_storage.models.CopyObjectDetails(
            destination_bucket=destination_bucket,
            destination_namespace=namespace,
            destination_object_name=destination_object_name,
            destination_region=signer.region,
            source_object_name=source_object_name
        ),
        wait_for_states=[
            oci.object_storage.models.WorkRequest.STATUS_COMPLETED,
            oci.object_storage.models.WorkRequest.STATUS_FAILED])
    if resp.data.status != "COMPLETED":
        raise Exception("cannot copy object {0} to bucket {1}".format(source_object_name, destination_bucket))
    else:
        resp = objstore.delete_object(namespace, source_bucket, source_object_name)
        logging.getLogger().info("Object {0} moved to Bucket {1}".format(source_object_name, destination_bucket))


def find_original_document(namespace, bucketName, resourceName, sourceBucket):
    exploded = resourceName.split('/')
    parentFolder = ("/".join(exploded[:-1]))+"/"
    fileName=exploded[len(exploded)-1]
    fileName=fileName.replace(namespace+"_"+sourceBucket+"_", "")
    originalFileName=fileName
    simplifiedResourceName=resourceName
    if fileName.endswith(".json"):
        # vision service bug replace extra suffix
        originalFileName = originalFileName.replace("_searchable_document.pdf","")
        # remove .json in the end
        originalFileName = originalFileName[:-5]
        simplifiedResourceName = originalFileName + ".json"
    if fileName.endswith(".pdf"):
        # vision service bug replace extra suffix
        originalFileName = originalFileName.replace("_searchable_document.pdf","")
        simplifiedResourceName = originalFileName + ".pdf"
        
    originalResourceId="/n/"+namespace+"/b/"+sourceBucket+"/o/"+originalFileName
    originalResourceIdHash=hashlib.md5(originalResourceId.encode('utf-8')).hexdigest()
    return {
        'resourceName':resourceName,
        'simplifiedResourceName':simplifiedResourceName,
        'originalFileName': originalFileName,
        'originalResourceId': originalResourceId,
        'originalResourceIdHash': originalResourceIdHash,
        'parentFolder':parentFolder
    }

def parse_output_file(config, signer, namespace, bucketName, resourceName, sourceBucket):
    os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    os_obj = os_client.get_object(namespace_name=namespace, bucket_name=bucketName, object_name=resourceName)

    #with open('out.txt', 'w', encoding='utf-8') as f:
    #    f.write(str(os_obj.data.content.decode('utf-8')))

    ai_out=json.loads(os_obj.data.content.decode('utf-8'))
    
    page_count=ai_out["documentMetadata"]["pageCount"]
    mime_type=ai_out["documentMetadata"]["mimeType"]
    document_type=ai_out["detectedDocumentTypes"][0]["documentType"]
    language_code=ai_out["detectedLanguages"][0]["languageCode"]
    
    original_document = find_original_document(namespace, bucketName, resourceName, sourceBucket)

    extracted_text = ""
    for page in ai_out['pages']:
        for line in page['lines']:
            #print(" {0} ".format(line['text']))
            extracted_text = extracted_text + line['text'] + "\n"

    return {
        'extracted_text': extracted_text,
        'document_type': document_type,
        'language_code': language_code,
        'page_count': page_count,
        'mime_type': mime_type,
        'original_file_name': original_document["originalFileName"],
        'original_resource_id':original_document["originalResourceId"],
        'resource_id_hash': original_document["originalResourceIdHash"],
        'simplified_resource_name': original_document["simplifiedResourceName"]
    }

def get_single_row(api_url, resource_id_hash):
    logging.getLogger().debug("Resource Id MD5 Hash: {0} ".format(resource_id_hash))
    res = requests.get(url=api_url+resource_id_hash)
    status_code = res.status_code
    logging.getLogger().debug("Get Sinle Row API Call Response.StatusCode: {0} Response.Reason: {1}".format(status_code, res.reason))
    if status_code not in [200]:
        raise Exception("Cannot query object with {0}, status code {1} and reason {2}".format(resource_id_hash, status_code, res.reason))
    return res.json()

def persist_data(api_url, json_data, headers):
    #res = requests.post(api_url, data=json.dumps(json_data), headers=headers)
    logging.getLogger().debug("Resource Id MD5 Hash: {0} ".format(json_data["resource_id_hash"]))
    res = requests.put(api_url + json_data["resource_id_hash"], json=json_data, headers=headers)
    status_code = res.status_code
    logging.getLogger().debug("Persist API Call Response.StatusCode: {0} Response.Reason: {1}".format(status_code, res.reason))
    # logging.getLogger().debug("API Url:{}".format(api_url + json_data["resource_id_hash"]))
    # logging.getLogger().debug("Headers:{}".format(json.dumps(headers)))
    # logging.getLogger().debug("Payload:{}".format(json.dumps(json_data)))
    if status_code not in [200, 201]: ##200: Updated, 201: Created
        raise Exception("Cannot persist object {0} on bucket {1}, status code {2} and reason {3}".format(json_data["resource_name"], json_data["bucket_name"], status_code, res.reason))


def handler(ctx, data: io.BytesIO = None):
    signer = oci.auth.signers.get_resource_principals_signer()
    config = ctx.Config()
    eventID = eventTime = compartmentId = compartmentName = resourceName = resourceId = namespace = bucketName = bucketId = api_url = ""
    processed_bucket = ""
    ai_vision_output_bucket = ""
    source_bucket = ""
    ## Get Config
    try:
        api_url = config["ords-base-url"]
        processed_bucket = config["processed-bucket"]
        ai_vision_output_bucket = config ["ai-vision-output-bucket"]
        source_bucket = config ["source-bucket"]
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
        logging.getLogger().error('Missing function config parameters: ords-base-url: ' + str(ex))
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

    if str(resourceName).endswith(".json") or str(resourceName).endswith(".pdf"):
        logging.getLogger().info("{0} will be processed ".format(resourceName))
        
        original_document = find_original_document(namespace, bucketName, resourceName, sourceBucket=source_bucket)
        logging.getLogger().info("Original document {}".format(original_document))

        # json file has required info, only parse and update when input is json
        # pdf files need to be just moved
        if str(resourceName).endswith(".json"):
            logging.getLogger().debug("Parse output json file")
            ai_data=parse_output_file(config, signer, namespace, bucketName, resourceName, sourceBucket=source_bucket)

            logging.getLogger().debug("Find related db row")
            db_row=get_single_row(api_url, ai_data["resource_id_hash"])
        
            logging.getLogger().debug("Update db row with new details")
            db_row['extracted_text']=ai_data["extracted_text"]
            db_row['document_type']=ai_data["document_type"]
            db_row['language_code']=ai_data["language_code"]
            db_row['page_count']=ai_data["page_count"]
            db_row['mime_type']=ai_data["mime_type"]
            db_row.pop('links', None)
        
            headers =  {'Content-Type':"application/json"}
            persist_data(api_url, db_row, headers)
        
        move_object(signer, namespace, 
            source_bucket = bucketName, 
            destination_bucket = processed_bucket, 
            source_object_name = resourceName, 
            destination_object_name = original_document["simplifiedResourceName"])
        
        if str(resourceName).endswith(".pdf"):
            delete_object(signer, namespace, bucket_name=bucketName, object_name=original_document['parentFolder'])
    else:
        logging.getLogger().info("{0} is not processed by this function".format(resourceName))

    return response.Response(
        ctx, response_data=json.dumps(
             {"status_code":"SUCCESS", "message": "Successfuly processed image {0}".format(resourceName)}),
        headers={"Content-Type": "application/json"}
    )

"""
"01GE7F0SM61BT0B18ZJ002A01T - root - INFO - 
ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaaf6u4cpd2ymlmcozgpiko3itw6xifqxtax6y26lzu4xya/
lrfymfp24jnl_documents-process-queue_ai-vision-document/
ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaalx7ogcku2mqgymlwsurt3fnvubvqud3gz7hax2mhtifq/
lrfymfp24jnl_documents-process-queue_ah_receipt.jpg_searchable_document.pdf.json will be processed "
##DEBUG
##logging.getLogger().setLevel(40)
config = oci.config.from_file("~/.oci/config","DEFAULT")
identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data

object_storage = oci.object_storage.ObjectStorageClient(config)
namespace=object_storage.get_namespace().data
logging.getLogger().info("namespace: {}".format(namespace))

signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )

api_url="https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"
bucketName="documents-process-queue"
resourceName="ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaa25df7oo734qj4hlyq62vhi5vmvnijtme6k2hc5xuaupa/lrfymfp24jnl_documents-process-queue_tbp-gZUiv3sMhpAvVNvtcvPT.jpg.json"

ai_data=parse_output_file(config, signer, namespace, bucketName, resourceName)
db_row=get_single_row(api_url, ai_data["resource_id_hash"])

db_row['extracted_text']=ai_data["extracted_text"]
db_row['document_type']=ai_data["document_type"]
db_row['language_code']=ai_data["language_code"]
db_row['page_count']=ai_data["page_count"]
db_row['mime_type']=ai_data["mime_type"]
db_row.pop('links', None)
print(db_row)
headers =  {'Content-Type':"application/json"}
persist_data(api_url, db_row, headers)

#curl --location 'https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/5275fe8ab85fd37fd1ae73b472e421f6' 
"""