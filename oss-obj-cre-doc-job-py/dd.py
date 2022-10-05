from asyncio.format_helpers import extract_stack
from http import client
import io
import json
import logging
from pyexpat import features
from sys import prefix
import uuid
import requests

import oci
from oci.config import get_config_value_or_default, validate_config
from oci.signer import Signer

"""
curl --location --request POST \
'https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/' \
--header 'Content-Type: application/json' \
--data-binary '{
  "resource_id": "1",
  "event_id": "1",
  "event_time": "2019-07-10T13:37:11Z",
  "compartment_id": "1",
  "compartment_name": "1",
  "resource_name": "obj name",
  "os_namespace": "lrfymfp24jnl",
  "bucket_name": "<VALUE>",
  "bucket_id": "<VALUE>",
  "extracted_text": "<VALUE>"
}'
def insert_data(api_url, json_data, headers):
    response = requests.post(api_url, data=json.dumps(json_data), headers=headers)
    print(response.status_code)
    if response.status_code != 201:
        raise Exception("Cannot insert object {0} on bucket {1}".format(json_data["resource_name"], json_data["bucket_name"]))
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
    with open('out.json', 'w', encoding='utf-8') as f:
        f.write(str(resp.data))
    #print(resp.data)

    if resp.status != 200:
        raise Exception("cannot analyze object {0} on bucket {1}".format(object_name, bucket_name))
    else:
        logging.getLogger().info("Object {0} bucket {1} analyzed".format(object_name, bucket_name))
        document_type=resp.data.detected_document_types[0].document_type
        language_code=resp.data.detected_languages[0].language_code
        page_count=resp.data.document_metadata.page_count
        mime_type=resp.data.document_metadata.mime_type
        print("document_type:{0}".format(document_type))
        print("language_code:{0}".format(language_code))
        extracted_text = ""
        for page in resp.data.pages:
            for line in page.lines:
                #print(" {0} ".format(line.text))
                extracted_text=extracted_text + line.text + "\n"
        print("extracted_text:{0}".format(extracted_text))
        ##
        ##print("inserting data")
        api_url = "https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"
        json_data = {
            "resource_id": "3",
            "event_id": "1",
            "event_time": "2019-07-10T13:37:11Z",
            "compartment_id": "1",
            "compartment_name": "1",
            "resource_name": object_name,
            "os_namespace": namespace,
            "bucket_name": bucket_name,
            "bucket_id": "<VALUE>",
            "extracted_text": extracted_text,
            "document_type":document_type,
            "language_code":language_code,
            "page_count":page_count
            }
        headers =  {"Content-Type":"application/json"}
        ##insert_data(api_url, json_data, headers)

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
    ##


def analyze_document_bulk(config, signer, namespace, bucket_name, object_name, prefix):
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
            output_location=oci.ai_vision.models.OutputLocation(bucket_name=bucket_name, namespace_name=namespace, prefix=prefix)
        )
    )
    document_job_id = resp.data.id
    ##"ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaak4f4qryfawxfcxzhsawhxnxtszy44vmyzi5jsixx2g7q/lrfymfp24jnl_documents-process-queue_ah_receipt.jpg.json"
    output_file_name=prefix+"/"+resp.data.id+"/"+namespace+"_"+bucket_name+"_"+object_name+".json"
    ##"ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaak4f4qryfawxfcxzhsawhxnxtszy44vmyzi5jsixx2g7q/lrfymfp24jnl_documents-process-queue_ah_receipt.jpg_searchable_document.pdf"
    searchable_document_name=prefix+"/"+resp.data.id+"/"+namespace+"_"+bucket_name+"_"+object_name+"_searchable_document.pdf"
    return {"document_job_id":document_job_id, "output_file_name":output_file_name, "searchable_document_name":searchable_document_name}


def create_object(config, signer, namespace, bucket_name, object_name, object_data):
    os_client = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    resp = os_client.put_object(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=object_name,
        put_object_body=object_data
    )
    print(json.dumps(resp.data))

print("Goodbye, World!")

config = oci.config.from_file("~/.oci/config","DEFAULT")
identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data
#print(user)

#signer = oci.auth.signers.get_resource_principals_signer()
#print(signer)

object_storage = oci.object_storage.ObjectStorageClient(config)
print(object_storage.get_namespace().data)

signer = Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )

namespace="lrfymfp24jnl"
bucket_name="documents-process-queue"
object_name="ah_receipt.jpg"
#ai_result = analyze_document_online(config, signer, "lrfymfp24jnl", "documents-process-queue", "ah_receipt.jpg")
#create_object(config, signer, namespace="lrfymfp24jnl", bucket_name="documents-process-queue", object_name="deneme.json", object_data=ai_result["raw_result_json"])
#print(json.dumps(resp.data, indent=4))
analyze_document_bulk(config, signer, namespace, bucket_name, object_name, prefix="ai-vision-document")
