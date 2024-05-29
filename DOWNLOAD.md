# PIFSC/ESD NOAA Cloud | How to Download
### Learn More about NOAA Open Data Dissemination(NODD) 
- NODD Homepage
  - https://www.noaa.gov/information-technology/open-data-dissemination
- PIFSC NODD
  - https://console.cloud.google.com/welcome?project=nmfs-trusted-images
  - PIFSC Cloud Console URL
    - https://console.cloud.google.com/storage/browser/nmfs_odp_pifsc
  - PIFSC GSUtil URL
    - gs://nmfs_odp_pifsc
  - PIFSC Bucket API
    - https://www.googleapis.com/storage/v1/b/nmfs_odp_pifsc/o
## Step 1: Install Gsutil
- Install:
  - https://cloud.google.com/storage/docs/gsutil_install
- Checkout the Quickstart:
  - https://cloud.google.com/storage/docs/discover-object-storage-gcloud
- More info | Google SDK Docs
  - https://cloud.google.com/storage/docs/discover-object-storage-gsutil
  - https://cloud.google.com/sdk/docs

 ### Download Notes
- Downloading 1 or more folders requires the google command-line tool.
- Only individual objects can be downloaded using the Cloud web Console.
- To download a folder or multiple objects at a time, you can run this code for the selected resources in the gsutil command line tool.

## Step 2: Run download Script
### Simple NODD Download Script Example 01
- uses rsync command for "synchronizing files between a computer and a storage drive and across networked computers by comparing the modification times and sizes of files."
- allows for stop and restart of the download
```
gsutil -m rsync -r "nmfs_odp_pifsc/PIFSC/ESD/ARP/Acoustics" C:\destination_folder_path
```
### Simple NODD Download Script Example 02
```
gsutil -m cp -r \
  "gs://nmfs_odp_pifsc/PIFSC/ESD/ARP/Acoustics" \
  .
```

### NODD for other NMFS Centers:
- https://console.cloud.google.com/storage/browser/nmfs_odp_afsc
- https://console.cloud.google.com/storage/browser/nmfs_odp_swfsc
- https://console.cloud.google.com/storage/browser/nmfs_odp_nefsc
- https://console.cloud.google.com/storage/browser/nmfs_odp_nwfsc
- https://console.cloud.google.com/storage/browser/noaa-passive-bioacoustic
- https://console.cloud.google.com/storage/browser/noaa-nidis-drought-gov-data
