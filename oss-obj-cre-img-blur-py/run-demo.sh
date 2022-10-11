#!/bin/bash
# Purpose: Display how powerful features can be implemented with Events and Functions
# Author: Fatih Keles <fatih.k.keles@oracle.com>
# 2022-10-07 - fkeles : Created
# ---------------------------------------------------------------------------
dry_run=false
export _input_bucket_name=auto-blur-images
# export _ords_url="https://gf5f9ffc50769d0-sitl8rh4u9o8ht3x.adb.uk-london-1.oraclecloudapps.com/ords/admin/os_text_extracts/"

# display message and pause 
pause(){
	local m="$@"
	echo "$m"
	read -p "Press [Enter] key to continue..." key
}

# Query object storage
query_object_storage(){
   i=0
   os_list=`oci os object list --bucket-name $_input_bucket_name | jq -r '.data[] | "\(.name) \(."'"time-created"'") " ' ` 
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
	curl -s --location $_ords_url | jq '.items[] | "\(.resource_name) \(.document_type) \(.page_count) \(.mime_type)" ' | column -t
   ##curl --location $_ords_url | jq '.items[] | "['"'\(.resource_name)'"', '"'\(.document_type)'"', '"'\(.page_count)'"', '"'\(.mime_type)'"']" '
   ##curl --location $_ords_url | jq '.items[] | "['''\(.resource_name)''', '''\(.document_type)''', '''\(.page_count)''', '''\(.mime_type)''']" '
}


echo 'Flow:'
echo '1. Delete previous demo data'
echo '3. Upload test files to object storage'
echo '4. Check object storage for results'
echo 
pause 'Starting Demo!'


# clear
# echo "############################################## 1. delete folder test-data ####################################################"
# i=0
# test_files=`ls sample-images-blurred/*.jpg sample-images-blurred/*.jpeg sample-images-blurred/*.tiff sample-images-blurred/*.png`
# for eachfile in $test_files
# do
#    let i=i+1
#    if [ "$dry_run" = false ] ; then
#       # echo 'Deleting' $eachfile
#       rm $eachfile
#    fi
# done
# echo 
# echo $i 'files deleted'
# pause

# clear
# echo "############################################## 2. delete object storage test-data ##############################################"
# i=0
# os_list=`oci os object list --bucket-name $_input_bucket_name | jq -r '.data[].name'`
# for eachfile in $os_list
# do
#    let i=i+1
#    echo 'Deleting object' $eachfile
#    if [ "$dry_run" = false ] ; then
#       oci os object delete --force --bucket-name $_input_bucket_name --object-name $eachfile
#    fi
# done
# echo 
# echo $i 'objects deleted'
# pause

# clear
# echo "############################################## 3. upload object storage test-data ###############################################"
# i=0
# current_dir=`pwd`
# cd sample-images
# test_files=`ls *.jpg *.jpeg *.tiff *.png`
# for eachfile in $test_files
# do
#    let i=i+1
#    echo 'Uploading' $eachfile
#    if [ "$dry_run" = false ] ; then
#       oci os object put --bucket-name $_input_bucket_name --file $eachfile --name $eachfile
#    fi
# done
# echo 
# echo $i 'files uploaded'
# cd $current_dir
# pause

# clear
# pause "Wait for Events service to invoke Functions"
# ##time_start=date "+%Y-%m-%d %H:%M%z"
# ##time_end=date --date='5 minutes' "+%Y-%m-%d %H:%M%z"
# ##oci logging-search search-logs --time-start $time_start --time-end $time_end --search-query 'search "ocid1.compartment.oc1..aaaaaaaapbatjdpgcbfpvwxmfkav5ijagbf7aepp5ln7xxlpl5ba347xukja/ocid1.loggroup.oc1.uk-london-1.amaaaaaadiwdpaqapxfulqbockvfnrblmeusb3jeiolicbx5ehl3l4gz3mcq" | sort by datetime desc'

# while :
# do
#    clear
#    echo "############################################## 4. check object storage test-data #################################################"
#    # query_object_storage 
#    oci os object list --bucket-name $_input_bucket_name | jq -r '.data[] | "\(.name) \(."'"time-created"'") \(."'"time-modified"'")" ' | column -t
#    read -r -p "Press r to Re-Query x to Exit Loop..." c
#    case $c in
#       r) echo "";;
#       x) break;;
# 		*) Pause "Press r or x"
#    esac
# done

clear
echo "############################################## 5. download object storage test-data ##############################################"
i=0
os_list=`oci os object list --bucket-name $_input_bucket_name | jq -r '.data[].name'`
for eachfile in $os_list
do
   let i=i+1
   echo 'Downloading object' $eachfile
   if [ "$dry_run" = false ] ; then
      oci os object get --bucket-name $_input_bucket_name --name $eachfile --file 'sample-images-blurred/'$eachfile
   fi
done
echo 
echo $i 'objects downloaded'
pause

echo "Completed!"