from http import client
import io
import json
import logging
import uuid

import oci
from oci.config import get_config_value_or_default, validate_config
from oci.signer import Signer

def analyze_document(config, signer, namespace, bucket_name, object_name):
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

analyze_document(config, signer, "lrfymfp24jnl", "document_process_queue", "ah_receipt.jpg")
#print(json.dumps(resp.data, indent=4))
