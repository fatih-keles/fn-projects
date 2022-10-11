import hashlib
import oci
import logging

def delete_object(config, signer, namespace, bucket_name, object_name):
    objstore = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    resp = objstore.delete_object(namespace, bucket_name, object_name)
    logging.getLogger().info("Object {0} deleted ".format(object_name))

def find_original_document(namespace, bucketName, resourceName):
    exploded = resourceName.split('/')
    parentFolder = ("/".join(exploded[:-1]))+"/"
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
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaa5mvxccaxkb6uv7yuxwimt3kjkh34efaozqvu4bmccy5a/lrfymfp24jnl_ocr-documents_Binder8.pdf.json",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaa5mvxccaxkb6uv7yuxwimt3kjkh34efaozqvu4bmccy5a/lrfymfp24jnl_ocr-documents_Binder8.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaabwvz6eyw6l4mxwb75hfyp3h6dnrwseqybiml2rkkydza/lrfymfp24jnl_ocr-documents_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaawhmjrchymoclawkwqogy6nmv3jtladp74vjfcch2djca/lrfymfp24jnl_ocr-documents_ah_receipt.jpg_searchable_document.pdf.json",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaabwvz6eyw6l4mxwb75hfyp3h6dnrwseqybiml2rkkydza/lrfymfp24jnl_ocr-documents_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaawhmjrchymoclawkwqogy6nmv3jtladp74vjfcch2djca/lrfymfp24jnl_ocr-documents_ah_receipt.jpg_searchable_document.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaad35xpjnarjwn4zk755c2oaudw7zdfxqr6uhjuo6l3rga/lrfymfp24jnl_ocr-documents_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaaoppio4nfnn6vnjw5ndtyv4jbsepxrnvva4weaokazblq/lrfymfp24jnl_ocr-documents_Bill-Of-Sales-1958-Chevy.tiff_searchable_document.pdf.json",
    # "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaad35xpjnarjwn4zk755c2oaudw7zdfxqr6uhjuo6l3rga/lrfymfp24jnl_ocr-documents_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaaoppio4nfnn6vnjw5ndtyv4jbsepxrnvva4weaokazblq/lrfymfp24jnl_ocr-documents_Bill-Of-Sales-1958-Chevy.tiff_searchable_document.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaagvnrieafvxepusnfieab62o666mriij65llui2ygsqnq/lrfymfp24jnl_ocr-documents_Binder1.pdf.json",
    # "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaagvnrieafvxepusnfieab62o666mriij65llui2ygsqnq/lrfymfp24jnl_ocr-documents_Binder1.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaaoppio4nfnn6vnjw5ndtyv4jbsepxrnvva4weaokazblq/lrfymfp24jnl_ocr-documents_Bill-Of-Sales-1958-Chevy.tiff.json",
    # "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaaoppio4nfnn6vnjw5ndtyv4jbsepxrnvva4weaokazblq/lrfymfp24jnl_ocr-documents_Bill-Of-Sales-1958-Chevy.tiff_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaav6jsegofv5mxubzilel5vh4kpk6mqjkwijpznzpwtydq/lrfymfp24jnl_ocr-documents_Ammendment2-Signed.pdf.json",
    # "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaav6jsegofv5mxubzilel5vh4kpk6mqjkwijpznzpwtydq/lrfymfp24jnl_ocr-documents_Ammendment2-Signed.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaawhmjrchymoclawkwqogy6nmv3jtladp74vjfcch2djca/lrfymfp24jnl_ocr-documents_ah_receipt.jpg.json",
    # "i-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaawhmjrchymoclawkwqogy6nmv3jtladp74vjfcch2djca/lrfymfp24jnl_ocr-documents_ah_receipt.jpg_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaa5z3aesvpyqaviapki3bbnpbv2iv2hrdybaq33ketzo7a/lrfymfp24jnl_ocr-documents_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaapedsa33gk63zkwpgtwrihgvorc7p3xtzomlvp5bny7gq/lrfymfp24jnl_ocr-documents_Bill-Of-Sales-1958-Chevy.tiff_searchable_document.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaa6s76msgxeqlyfx7zcjrssxx44ymhyvvsmua5une2mvcq/lrfymfp24jnl_ocr-documents_Binder1.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaaou7hjarts3uqkb45ugkbarhlgq2b3h4cd74wl2irvp4a/lrfymfp24jnl_ocr-documents_ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaauysnydv5abeltihtix2gphcdspn6af6bek6mmmfrx4cq/lrfymfp24jnl_ocr-documents_ah_receipt.jpg_searchable_document.pdf.json",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaatsj3a6lbhk7kkpot5ouf5nuhgurumfjjahtlwq7ctf4a/lrfymfp24jnl_ocr-documents_Ammendment2-Signed.pdf_searchable_document.pdf",
    "ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaavqazzlmr7zchidfcwozpmbpsrmwjvdio67hqlyu3yawa/lrfymfp24jnl_ocr-documents_Binder8.pdf_searchable_document.pdf"
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

bucket_name=bucketName
object_name="ai-vision-document/ocid1.aivisiondocumentjob.oc1.uk-london-1.amaaaaaa74akfsaapzhmbi7ap5he6hx5wedmhmzyffjqgjatpyixsphj7aoq/"
delete_object(config, signer, namespace, bucket_name, object_name)