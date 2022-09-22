## deploy application 
fn deploy --app document-processing-application

## upload test data
export _bucket_name=document_process_queue
export _file_name=func.py
export _object_name=tbp-aaaaaaaapbatjdpgcbfpvwxmfkav5ijagbf7aepp5ln7xxlpl5ba347xukja.bin

oci os object delete --force --bucket-name $_bucket_name --object-name $_object_name
oci os object put --bucket-name $_bucket_name --file $_file_name --name $_object_name

## oci os object copy --bucket-name $bucket_name --destination-bucket $destination_bucket --source-object-name $source_object_name