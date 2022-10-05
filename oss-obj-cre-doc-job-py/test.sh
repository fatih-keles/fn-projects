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

## create application 
#oci fn application create --generate-full-command-json-input
#oci fn application create --generate-param-json-input subnet-ids subnet-ids
#oci fn application create --display-name "document-processing-application2" --compartment-id "ocid1.compartment.oc1..aaaaaaaapbatjdpgcbfpvwxmfkav5ijagbf7aepp5ln7xxlpl5ba347xukja" --subnet-ids ["ocid1.subnet.oc1.uk-london-1.aaaaaaaam5hdpn7ncpwvqeqctfnmrpgfixcp7ar7fpoextaa36vn7yre7waq"]

## deploy application 
fn deploy --app document-processing-application
fn config function document-processing-application oss-obj-cre-doc-job-py ords-base-url "https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"
fn config function document-processing-application oss-obj-cre-doc-job-py log-level "DEBUG"
fn config function document-processing-application oss-obj-cre-doc-job-py processed-bucket "documents-processed"


## upload test data
export _input_bucket_name=documents-process-queue
export _input_file_name=analyze-document/online/ah_receipt.jpg
export _input_object_name=tbp-`tr -dc A-Za-z0-9 </dev/urandom | head -c 20 ; echo ''`.jpg

##oci os object list --bucket-name documents-process-queue | jq .data[].name
##oci os object delete --force --bucket-name $_input_bucket_name --object-name $_input_object_name
oci os object put --bucket-name $_input_bucket_name --file $_input_file_name --name $_input_object_name

#export _input_file_name=analyze-document/online/Bill-Of-Sales-1958-Chevy.tiff
#export _input_object_name=tbp-`tr -dc A-Za-z0-9 </dev/urandom tbb*| head -c 20 ; echo ''`.tiff
#oci os object put --bucket-name $_input_bucket_name --file $_input_file_name --name $_input_object_name

#export _input_file_name=analyze-document/online/Ammendment2-Signed.pdf
#export _input_object_name=tbp-`tr -dc A-Za-z0-9 </dev/urandom | head -c 20 ; echo ''`.pdf
#oci os object put --bucket-name $_input_bucket_name --file $_input_file_name --name $_input_object_name

## oci os object copy --bucket-name $bucket_name --destination-bucket $destination_bucket --source-object-name $source_object_name

## Vision Service Processing Limits 
## Supported File Formats JPEG, PNG, PDF, and TIFF
## Maximum File Size: Single request = 5 MB, Batch request= 500 MB/document
## Maximum Document Count: Single request = Five pages, Batch request = 2,000 pages per document
## oci ai-vision analyze-document --document file://analyze-document/online/document.json --features file://analyze-document/online/features.json
## cat output2.json | jq '.data.pages[].lines[].text'


##curl --location 'https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/' | jq

#oci ai-vision document-job create --input-location file://input-location.json --features file://features.json --output-location file://output-location.json
#cat out.json | jq '.pages[].words[].text'
#cat out.json | jq '.pages[].lines[].text'

#oci os object list --bucket-name documents-process-queue | jq .data[].name
#oci os object delete --force --bucket-name documents-process-queue --object-name 

## oci db autonomous-database get --autonomous-database-id ocid1.autonomousdatabase.oc1.uk-london-1.anwgiljrdiwdpaqa2ra3d6uhhyvxxbu6briodswvgkxjhvi6zvxqsphrayna
## oci db autonomous-database start --autonomous-database-id ocid1.autonomousdatabase.oc1.uk-london-1.anwgiljrdiwdpaqa2ra3d6uhhyvxxbu6briodswvgkxjhvi6zvxqsphrayna