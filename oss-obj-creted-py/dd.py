from asyncio.format_helpers import extract_stack
from http import client
import io
import json
import logging
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
"""
def insert_data(api_url, json_data, headers):
    response = requests.post(api_url, data=json.dumps(json_data), headers=headers)
    print(response.status_code)
    if response.status_code != 201:
        raise Exception("Cannot insert object {0} on bucket {1}".format(json_data["resource_name"], json_data["bucket_name"]))
    

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
    with open('out.txt', 'w', encoding='utf-8') as f:
        f.write(str(resp.data))
    #print(resp.data)

    if resp.status != 200:
        raise Exception("cannot analyze object {0} on bucket {1}".format(object_name, bucket_name))
    else:
        logging.getLogger().info("Object {0} bucket {1} analyzed".format(object_name, bucket_name))
        document_type=resp.data.detected_document_types[0].document_type
        language_code=resp.data.detected_languages[0].language_code
        page_count=resp.data.document_metadata.page_count
        print("document_type:{0}".format(document_type))
        print("language_code:{0}".format(language_code))
        extracted_text = ""
        for page in resp.data.pages:
            for line in page.lines:
                #print(" {0} ".format(line.text))
                extracted_text=extracted_text.join([line.text, " "]) 
        print("extracted_text:{0}".format(extracted_text))
        ##
        print("inserting data")
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
        insert_data(api_url, json_data, headers)
    ##


def analyze_document_bulk(config, signer, namespace, bucket_name, object_name):
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
            ),
            output_location=oci.ai_vision.models.OutputLocation()
        ),
        opc_request_id=uuid.uuid4().hex
    )

    print(resp.status)
    print(resp.request_id)
    with open('out.txt', 'w', encoding='utf-8') as f:
        f.write(str(resp.data))
    #print(resp.data)
    if resp.status != 200:
        raise Exception("cannot analyze object {0} on bucket {1}".format(object_name, bucket_name))
    else:
        logging.getLogger().info("Object {0} bucket {1} analyzed".format(object_name, bucket_name))
        print("document_type:{0}".format(resp.data.detected_document_types[0].document_type))
        print("language_code:{0}".format(resp.data.detected_languages[0].language_code))
        page_count=resp.data.document_metadata.page_count
        for page in resp.data.pages:
            for line in page.lines:
                print(" {0} ".format(line.text))


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

analyze_document_online(config, signer, "lrfymfp24jnl", "document_process_queue", "ah_receipt.jpg")
#print(json.dumps(resp.data, indent=4))
