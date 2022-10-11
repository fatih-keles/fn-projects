import io
import json
import oci
import logging
import requests
import uuid
import hashlib
import sys, traceback

from fdk import response

def persist_data(api_url, json_data, headers):
    #res = requests.post(api_url, data=json.dumps(json_data), headers=headers)
    logging.getLogger().debug("Resource Id MD5 Hash: {0} ".format(json_data["resource_id_hash"]))
    res = requests.put(api_url + json_data["resource_id_hash"], json=json_data, headers=headers)
    status_code = res.status_code
    logging.getLogger().debug("Persist API Call Response.StatusCode: {0} Response.Reason: {1}".format(status_code, res.reason))
    logging.getLogger().debug("API Url:{}".format(api_url + json_data["resource_id_hash"]))
    logging.getLogger().debug("Headers:{}".format(json.dumps(headers)))
    logging.getLogger().debug("Payload:{}".format(json.dumps(json_data)))
    if status_code not in [200, 201]: ##200: Updated, 201: Created
        raise Exception("Cannot persist object {0} on bucket {1}, status code {2} and reason {3}".format(json_data["resource_name"], json_data["bucket_name"], status_code, res.reason))

def analyze_document_bulk(config, signer, namespace, bucket_name, object_name, output_bucket, prefix):
    ai_vision_client = oci.ai_vision.AIServiceVisionClient(config=config, signer=signer)
    resp = ai_vision_client.create_document_job(
        create_document_job_details=oci.ai_vision.models.CreateDocumentJobDetails(
            input_location=oci.ai_vision.models.ObjectListInlineInputLocation(
                object_locations=[
                    oci.ai_vision.models.ObjectLocation(bucket_name=bucket_name, namespace_name=namespace, object_name=object_name)
                ]
            ),
            features=[
                oci.ai_vision.models.DocumentClassificationFeature(max_results=5),
                oci.ai_vision.models.DocumentLanguageClassificationFeature(max_results=5),
                oci.ai_vision.models.DocumentTextDetectionFeature(generate_searchable_pdf=True)
            ],
            output_location=oci.ai_vision.models.OutputLocation(bucket_name=output_bucket, namespace_name=namespace, prefix=prefix)
        )
    )
    document_job_id = resp.data.id
    logging.getLogger().debug("Document Job Id: {0} ".format(document_job_id))
    #ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaak4f4qryfawxfcxzhsawhxnxtszy44vmyzi5jsixx2g7q/lrfymfp24jnl_documents-process-queue_ah_receipt.jpg.json"
    #ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaakfhqpcjxv4bswye3n5evltyyvpt6j3ke4e3znavj5xjq/lrfymfp24jnl_documents-process-queue_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaarxgw6ituahcsrk2kryubsfw4c2lgcafhhah5n3w7fpka/lrfymfp24jnl_documents-process-queue_Bill-Of-Sales-1958-Chevy.tiff_searchable_document.pdf.json
    output_file_name=prefix+"/"+resp.data.id+"/"+namespace+"_"+bucket_name+"_"+object_name+".json"
    logging.getLogger().debug("Output File Name: {0} ".format(output_file_name))
    #ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaak4f4qryfawxfcxzhsawhxnxtszy44vmyzi5jsixx2g7q/lrfymfp24jnl_documents-process-queue_ah_receipt.jpg_searchable_document.pdf"
    #ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaakfhqpcjxv4bswye3n5evltyyvpt6j3ke4e3znavj5xjq/lrfymfp24jnl_documents-process-queue_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaarxgw6ituahcsrk2kryubsfw4c2lgcafhhah5n3w7fpka/lrfymfp24jnl_documents-process-queue_Bill-Of-Sales-1958-Chevy.tiff_searchable_document.pdf_searchable_document.pdf
    searchable_document_name=prefix+"/"+resp.data.id+"/"+namespace+"_"+bucket_name+"_"+object_name+"_searchable_document.pdf"
    logging.getLogger().debug("Searchable Document Name: {0} ".format(searchable_document_name))
    return {"document_job_id":document_job_id, "output_file_name":output_file_name, "searchable_document_name":searchable_document_name}

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
    
    logging.getLogger().info("Analyze API Call Response.StatusCode: {0} ".format(resp.status))
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
        mime_type=resp.data.document_metadata.mime_type
        logging.getLogger().info("document_type:{0}".format(document_type))
        logging.getLogger().info("language_code:{0}".format(language_code))
        extracted_text = ""
        for page in resp.data.pages:
            for line in page.lines:
                #print(" {0} ".format(line.text))
                extracted_text = extracted_text + line.text + "\n"
        logging.getLogger().debug("extracted_text:{0}".format(extracted_text))
        ## words can also be extracted to build a search index

        return_values={
            "document_type":document_type, 
            "language_code":language_code, 
            "mime_type":mime_type, 
            "page_count":page_count, 
            "extracted_text":extracted_text,
            "raw_result_json":str(resp.data)
            }
        logging.getLogger().info("Returning values : {0} ".format(json.dumps(return_values)))
        return return_values

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

def create_object(signer, namespace, bucket_name, object_name, object_data):
    os_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    resp = os_client.put_object(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=object_name,
        put_object_body=object_data
    )
    print(resp.data)

def handler(ctx, data: io.BytesIO = None):
    signer = oci.auth.signers.get_resource_principals_signer()
    config = ctx.Config()
    eventID = eventTime = compartmentId = compartmentName = resourceName = resourceId = namespace = bucketName = bucketId = api_url = ""
    ai_vision_output_bucket = ""
    ## Get Config
    try:
        #input_bucket = config["input-bucket"]
        #processed_bucket = config["processed-bucket"]
        ## api_url = "https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"
        api_url = config["ords-base-url"]
        ai_vision_output_bucket = config["ai-vision-output-bucket"]
        #schema = config["db-schema"]
        #dbuser = config["db-user"]
        #dbpwd = config["dbpwd-cipher"]
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
        logging.getLogger().error('Missing function config parameters: bucket_name, api_url, schema, dbuser, dbpwd: ' + str(ex))
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
        logging.getLogger().error('Error parsing json payload: ' + str(ex))
        raise

    if 1==2:
        logging.getLogger().info("Analyzing object")
        ai_result = analyze_document_online(config=config, signer=signer, namespace=namespace, bucket_name=bucketName, object_name=resourceName)

        logging.getLogger().info("Moving object to processed bucket")
        move_object(signer, namespace=namespace, source_bucket=bucketName, destination_bucket=processed_bucket, object_name=resourceName)

    logging.getLogger().info("Create document analyzing job")
    ai_result = analyze_document_bulk(config, signer, namespace, bucket_name=bucketName, object_name=resourceName, output_bucket= ai_vision_output_bucket, prefix="ai-vision-document")

    logging.getLogger().info("Persisting data")
    json_data = {
        'resource_id_hash': hashlib.md5(resourceId.encode('utf-8')).hexdigest(),
        'resource_id': resourceId,
        'event_id': eventID,
        'event_time': eventTime,
        'compartment_id': compartmentId,
        'compartment_name': compartmentName,
        'resource_name': resourceName,
        'os_namespace': namespace,
        'bucket_name': bucketName,
        'bucket_id': bucketId,
        'extracted_text': "",
        'document_type': "",
        'language_code': "",
        'page_count': 0,
        'mime_type': "",
        'processing_job_id': ai_result['document_job_id'],
        'output_file_name': ai_result['output_file_name'],
        'searchable_document_name': ai_result['searchable_document_name']
        }
    headers =  {'Content-Type':"application/json"}
    persist_data(api_url, json_data, headers)

    return response.Response(
        ctx, response_data=json.dumps(
            {"status_code":"SUCCESS", "message": "Successfuly processed image {0}".format(resourceName)}),
        headers={"Content-Type": "application/json"}
    )

