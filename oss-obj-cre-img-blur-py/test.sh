## deploy application 
fn --verbose deploy --app  document-processing-application
#fn config function document-processing-application oss-obj-cre-img-blur-py ords-base-url "https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"
fn config function document-processing-application oss-obj-cre-img-blur-py log-level "DEBUG"
# fn config function document-processing-application oss-obj-cre-img-blur-py FDK_DEBUG 1
##fn config function document-processing-application oss-obj-pro-doc-job-res-py processed-bucket "documents-processed"

export _input_bucket_name=auto-blur-images
export _input_file_name=us.jpeg
export _input_object_name=us.jpeg

oci os object list --bucket-name $_input_bucket_name | jq -r '.data[] | "\(.name)" '
oci os object delete --force --bucket-name $_input_bucket_name --object-name $_input_object_name
oci os object put --bucket-name $_input_bucket_name --file $_input_file_name --name $_input_object_name


# cat sample-event.json | fn --verbose invoke document-processing-application oss-obj-cre-img-blur-py

##cat sample-event.json | python3 func.py