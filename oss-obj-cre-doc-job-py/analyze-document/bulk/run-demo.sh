#!/bin/bash
# Purpose: Display how OCI Vision OCR feature can be used with Events, Functions and ORDS
# Author: Fatih Keles <fatih.k.keles@oracle.com>
# 2022-09-30 - fkeles : Created
# ---------------------------------------------------------------------------
dry_run=false
export _input_bucket_name=ocr-documents
export _input_bucket_name2=ocr-extracts
export _input_bucket_name3=ocr-documents-temp
export _ords_url="https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"

# display message and pause 
pause(){
	local m="$@"
	echo "$m"
	read -p "Press [Enter] key to continue..." key
}

# Query object storage
query_object_storage(){
   i=0
   os_list=`oci os object list --bucket-name $@ | jq -r '.data[] | "\(.name)" '`
   for eachfile in $os_list
   do
      let i=i+1
      echo $eachfile
   done
   echo 
   echo $i 'objects found'
}

# Query database
query_database(){
   echo 'FileName                       FileType #Pages MimeType'
	curl -s --location $_ords_url | jq -r '.items[] | "\(.resource_name) \(.document_type) \(.page_count) \(.mime_type)" ' | column -t
   ##curl --location $_ords_url | jq '.items[] | "['"'\(.resource_name)'"', '"'\(.document_type)'"', '"'\(.page_count)'"', '"'\(.mime_type)'"']" '
   ##curl --location $_ords_url | jq '.items[] | "['''\(.resource_name)''', '''\(.document_type)''', '''\(.page_count)''', '''\(.mime_type)''']" '
}


echo 'Flow:'
echo '1. Delete database entries'
echo '2. Delete object storage data'
echo '3. Upload test files to object storage'
echo '4. Check object storage for OCR results'
echo '5. Check database results'
echo 
pause 'Starting Demo!'


clear
echo "############################################## 0. start database if it is not already running ###################################"
db_state=`oci db autonomous-database get --autonomous-database-id ocid1.autonomousdatabase.oc1.uk-london-1.anwgiljrdiwdpaqa2ra3d6uhhyvxxbu6briodswvgkxjhvi6zvxqsphrayna | jq -r '.data["lifecycle-state"]'`
echo 'Database State' $db_state
if [ $db_state != 'AVAILABLE' ];
then
   oci db autonomous-database start --autonomous-database-id ocid1.autonomousdatabase.oc1.uk-london-1.anwgiljrdiwdpaqa2ra3d6uhhyvxxbu6briodswvgkxjhvi6zvxqsphrayna
   echo 
   pause 'Starting ATP!'

   while :
   do
      clear
      echo "############################################## 0. check database started ####################################################"
      oci db autonomous-database get --autonomous-database-id ocid1.autonomousdatabase.oc1.uk-london-1.anwgiljrdiwdpaqa2ra3d6uhhyvxxbu6briodswvgkxjhvi6zvxqsphrayna | jq -r '.data["lifecycle-state"]'
      read -r -p "Press r to Re-Query x to Exit Loop..." c
      case $c in
         r) echo "";;
         x) break;;
         *) Pause "Press r or x"
      esac
   done
fi
echo 
pause

clear
echo "############################################## 1. delete database test-data ####################################################"
i=0
db_list=`curl --location $_ords_url | jq -r '.items[].links[].href'`
for eachfile in $db_list
do
   let i=i+1
   if [ "$dry_run" = false ] ; then
      curl --request "DELETE" --location $eachfile 
      #pause
   fi
done
echo 
echo $i 'records deleted'
pause

clear
echo "############################################## 2. delete object storage test-data ##############################################"
i=0
os_list=`oci os object list --bucket-name $_input_bucket_name | jq -r '.data[].name'`
for eachfile in $os_list
do
   let i=i+1
   echo 'Deleting object' $eachfile
   if [ "$dry_run" = false ] ; then
      oci os object delete --force --bucket-name $_input_bucket_name --object-name $eachfile
   fi
done
echo 
echo $i 'objects deleted in' $_input_bucket_name

echo 
## also delete processed folder
i=0
os_list=`oci os object list --bucket-name $_input_bucket_name2 | jq -r '.data[].name'`
for eachfile in $os_list
do
   let i=i+1
   echo 'Deleting object' $eachfile
   if [ "$dry_run" = false ] ; then
      oci os object delete --force --bucket-name $_input_bucket_name2 --object-name $eachfile
   fi
done
echo 
echo $i 'objects deleted in' $_input_bucket_name2

echo 
## also delete temp folder
i=0
os_list=`oci os object list --bucket-name $_input_bucket_name3 | jq -r '.data[].name'`
for eachfile in $os_list
do
   let i=i+1
   echo 'Deleting object' $eachfile
   if [ "$dry_run" = false ] ; then
      oci os object delete --force --bucket-name $_input_bucket_name3 --object-name $eachfile
   fi
done
echo 
echo $i 'objects deleted in' $_input_bucket_name3
pause

clear
echo "############################################## 3. upload object storage test-data ###############################################"
i=0
test_files=`ls *.jpg *.tiff *.pdf`
for eachfile in $test_files
do
   let i=i+1
   echo 'Uploading' $eachfile
   if [ "$dry_run" = false ] ; then
      oci os object put --bucket-name $_input_bucket_name --file $eachfile --name 'tbp-'$eachfile
   fi
done
echo 
echo $i 'files uploaded'
pause

clear
pause "Wait for Events service to invoke Functions"
##time_start=date "+%Y-%m-%d %H:%M%z"
##time_end=date --date='5 minutes' "+%Y-%m-%d %H:%M%z"
##oci logging-search search-logs --time-start $time_start --time-end $time_end --search-query 'search "ocid1.compartment.oc1..aaaaaaaapbatjdpgcbfpvwxmfkav5ijagbf7aepp5ln7xxlpl5ba347xukja/ocid1.loggroup.oc1.uk-london-1.amaaaaaadiwdpaqapxfulqbockvfnrblmeusb3jeiolicbx5ehl3l4gz3mcq" | sort by datetime desc'

bucket_of_interest=$_input_bucket_name
while :
do
   clear
   echo "############################################## 4. check object storage test-data #################################################"
   query_object_storage $bucket_of_interest
   read -r -p "Press s 'Source' d 'Destination' t 'Temp' bucket, x to Exit Loop..." c
   case $c in
      s) bucket_of_interest=$_input_bucket_name; echo "";;
      d) bucket_of_interest=$_input_bucket_name2; echo "";;
      t) bucket_of_interest=$_input_bucket_name3; echo "";;
      x) break;;
		*) Pause "Press s,d or x"
   esac
done

while :
do
   clear
   echo "############################################## 5. check database test-data ######################################################"
   query_database 
   read -r -p "Press r to Re-Query x to Continue..." c
   case $c in
      r) echo "";;
      x) break;;
		*) Pause "Press r or x"
   esac
done

echo "Completed!"