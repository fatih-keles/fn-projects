## Create a Dynamic Group DGFNforFatihKeles
#ALL {resource.type = 'fnfunc', resource.compartment.id = 'ocid1.compartment.oc1..aaaaaaaapbatjdpgcbfpvwxmfkav5ijagbf7aepp5ln7xxlpl5ba347xukja'}

## Add Policy 
#Allow dynamic-group DGFNforFatihKeles to manage objects in compartment FatihKeles
#Allow dynamic-group DGFNforFatihKeles> to buckets objects in compartment FatihKeles
#Allow service objectstorage-uk-london-1 to manage object-family in tenancy

## Update and install Python SDK
#sudo apt-get update
#sudo apt install python3-pip
#python3 -m pip install oci oci-cli

## deploy application 
fn deploy --app document-processing-application

## upload test data
export _bucket_name=document_process_queue
export _file_name=analyze-document/ah_receipt.jpg
export _object_name=tbp-aaaaaaaapbatjdpgcbfpvwxmfkav5ijagbf7aepp5ln7xxlpl5ba347xukja.bin

oci os object delete --force --bucket-name $_bucket_name --object-name $_object_name
oci os object put --bucket-name $_bucket_name --file $_file_name --name $_object_name

## oci os object copy --bucket-name $bucket_name --destination-bucket $destination_bucket --source-object-name $source_object_name
## oci ai-vision analyze-document --document file://analyze-document/document.json --features file://analyze-document/features.json
## cat output2.json | jq '.data.pages[].lines[].text'