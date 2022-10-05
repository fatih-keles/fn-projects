## deploy application 
fn deploy --app document-processing-application
fn config function document-processing-application oss-obj-pro-doc-job-res-py ords-base-url "https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"
fn config function document-processing-application oss-obj-pro-doc-job-res-py log-level "DEBUG"
##fn config function document-processing-application oss-obj-pro-doc-job-res-py processed-bucket "documents-processed"

cat sample-event.json | fn invoke document-processing-application oss-obj-pro-doc-job-res-py

