import hashlib
import oci
import logging

def delete_object(config, signer, namespace, bucket_name, object_name):
    objstore = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    resp = objstore.delete_object(namespace, bucket_name, object_name)
    logging.getLogger().info("Object {0} deleted ".format(object_name))

def find_original_document(namespace, bucketName, resourceName):
    exploded = resourceName.split('/')
    parentFolder = "/".join(exploded[:-1])+"/"
    fileName=exploded[len(exploded)-1]
    fileName=fileName.replace(namespace+"_"+bucketName+"_", "")
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
        
    originalResourceId="/n/"+namespace+"/b/"+bucketName+"/o/"+originalFileName
    originalResourceIdHash=hashlib.md5(originalResourceId.encode('utf-8')).hexdigest()
    return {
        # "resourceName":resourceName,
        "simplifiedResourceName":simplifiedResourceName,
        "originalFileName": originalFileName,
        # "originalResourceId": originalResourceId,
        # "originalResourceIdHash": originalResourceIdHash,
        'parentFolder':parentFolder
    }


obj_list = [
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaajbc74g2oqww4sftaoxgqdgqgafphzyrd2egpczke5vgq/lrfymfp24jnl_ocr-documents_tbp-Binder1.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaaqr2sagnwsacahme2zmuzuzrn7droqxsgfix2n62cozxa/lrfymfp24jnl_ocr-documents_tbp-Ammendment2-Signed.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaavhrhiy4xyejc6owanxcjlsxb3hnh6hoqinxw6rwqmmxa/lrfymfp24jnl_ocr-documents_tbp-Binder8.pdf_searchable_document.pdf"
]

namespace = "lrfymfp24jnl"
bucketName = "ocr-documents"

a=['1','2','3','4','5']
print("/".join(a[:-1]))

for obj in obj_list:
    print(find_original_document(namespace, bucketName, obj))


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

bucket_name="ocr-documents"
object_name="ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaapzhmbi7ap5he6hx5wedmhmzyffjqgjatpyixsphj7aoq"
# delete_object(signer, namespace, bucket_name, object_name)