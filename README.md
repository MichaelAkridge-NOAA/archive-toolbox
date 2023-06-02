<img align="right" src="_docs/icons/logo_archive_toolboxv3_500.png" alt="Manifest Tool" >

# ESD/ARP Archive Toolbox
Collection of Tools, Workflows and Processes to help Facilitate Archiving Scientific Data.
* Code Language: Python 3
* Contact: Michael.Akridge@noaa.gov
# Table of Contents
1. **[Archive Tools](#archive-tools)**
    * [File Copy Tool](#file-copy-tool)
    * [Folder Stats Tool](#folder-stats-tool)
    * [Garmin GPS File(GPX)Converter](#garmin-gps-filegpxconverter)
    * [Batch HEIC/HEIF to JPG Converter](#batch-heicheif-to-jpg-converter)
    * [Archive Manifest File Tool](#archive-manifest-file-tool)
    * [Other Archive Tools](#other-archive-tools)
2. **[Google Cloud Platform Upload Tools](#google-cloud-platform-upload-tools)**
    * [NOAA Open Data Dissemination (NODD) Workflow](#noaa-open-data-dissemination-nodd-workflow)
    * [NODD GUI Upload Tool](#nodd-gui-upload-tool)
    * [Simple NODD Upload Script Example ](#simple-nodd-upload-script-example)
    * [Simple NODD Download Script Example](#simple-nodd-download-script-example)
    * [NODD Details](#nodd-details)
***

# Archive Tools
<a href="./toolbox/file-copy-tool"><img align="right" src="./_docs/icons/sfm_toolbox_tool_00.png" alt="File Copy" width=400px></a>

## <a href="./toolbox/file-copy-tool"> File Copy Tool</a>
File copy tool will copy files and directories from one place to another. 
* It uses a subprocess to call a windows robust file copy command
* The app will skip any existing files in a destination directory
* It will also run multi-threaded for performance
* If a copy process is interrupted, then simply run again since it also has the ability to restart the transfer.
- NOTE: Multiplatform versions available 

<br clear="right"/>

<a href="./toolbox/folder-stats-tool"><img align="right" src="./_docs/icons/sfm_toolbox_tool_02.png" alt="Folder Stats" width=400px></a>

## <a href="./toolbox/folder-stats-tool"> Folder Stats Tool</a>
* Lightweight,python based, tool to gather folder stats like name, path, and size
* Exports a CSV of folder stats

<br clear="right"/>


<a href="./toolbox/garmin-gps-file-converter"><img align="right" src="./toolbox/garmin-gps-file-converter/_docs/s01.png" alt="garmin-gps-file-converter
" width=400px></a>

## <a href="./toolbox/garmin-gps-file-converter"> Garmin GPS File(GPX)Converter</a>
* Tool to convert Garmin GPS files(GPX) to standard TXT file format

<br clear="right"/>


<a href="./toolbox/HEIC_HEIF_converter"><img align="right" src="./toolbox/HEIC_HEIF_converter/_docs/s1.png" alt="HEIC_HEIF_converter" width=400px></a>

## <a href="./toolbox/HEIC_HEIF_converter"> Batch HEIC/HEIF to JPG Converter</a>
* Tool to batch convert HEIC/HEIF files to standard JPG file format

<br clear="right"/>


<a href="./toolbox/archive-manifest-file-tool"><img align="right" src="./_docs/icons/sfm_toolbox_tool_01.png" alt="Manifest Tool" width=400px></a>

## <a href="./toolbox/archive-manifest-file-tool"> Archive Manifest File Tool </a>
* Tool to Verify or Generate Archive Manifest Files 
* Required when sending archive packages
### Manifest File Details  
* A separate manifest file is required for every file that is transferred
* A manifest file contains three text values comma delimited on one line with no spaces for each submitted file.
```
<file_name>,<file_md5_checksum>,<file_size_in_bytes>
```
* The manifest file name pattern is the name of the associated data file with an added '.mnf'.
```
<file_name>.mnf
```
<br clear="right"/>

## Other Archive Tools
### PIFSC Centralized Data Tools - NCEI Tools Libary 
* PHP based tools. Data packager, bagit data packager, and submission manifest tools. 
* placeholder - link coming soon - placeholder
### Send2NCEI(S2N) 
* Use Send2NCEI to submit non-repeating or single delivery data less than 20 GB.
* https://www.ncei.noaa.gov/archive/send2ncei/
### Advanced Tracking and Resource Tool for Archive Collections (ATRAC)
* Use to submit repeating or multiple delivery data, or data that exceeds 20 GB.
* https://www.ncdc.noaa.gov/atrac/guidelines.html
----------

# Google Cloud Platform Upload Tools
### NOAA Open Data Dissemination (NODD) Workflow
![](./_docs/icons/nodd_workflow.png "")

### <a href="./toolbox/NODD_Upload_Tool/nodd_upload_tool.py"> NODD GUI Upload Tool </a>
<img src="_docs/icons/nodd_app_01.png" alt="NODD Upload Tool" >

## Requirements 
* GSUTIL backend: https://cloud.google.com/storage/docs/gsutil_install
* GCP Storage Bucket Permissions
* Python 3 and various packages

## Tool Details 
* syncs local data to Google Cloud Platform Storage using Google's gsutil backend
* Customizable gsutil command generation
* Logging and output message management
* Configurable parameters including dry run, multi-threading, and recursion
* A graphical user interface (GUI) is built using the Gooey library.
* Users can interact with the GUI to specify the source and destination paths, adjust threading, select a dry run, and decide whether to print or run the gsutil command.
* The main function fetches user input, configures the logger, and executes the copy process or prints the gsutil command based on user preference.

### Simple NODD Upload Script Example

```
gsutil -o "GSUtil:throttle_bandwidth=625000" -m rsync -r -n 
-x "(^.*(?<!\.JPG)$)|(.*_archive.*|.*_YEAR.*|.*ISLAND.*|.*SITE-ID.*|.*SITE_PHOTOS.*|.*uncorrected.*|.*MISC.*|.*DARK.*|.*Products.*)" 
C:\nodd\test gs://nmfs_odp_pifsc/PIFSC/ESD/ARP/test
```

<details> 
<summary>--- read: breakdown of what each flag and option does:</summary>

- <b>gsutil</b>: This is the command-line tool for interacting with Google Cloud Storage. https://cloud.google.com/storage/docs/gsutil
- <b>-o "GSUtil:parallel_thread_count=4" </b> if use multi-threading, limit bandwidth usage with this flag
- <b>-m</b>: This flag enables multi-threading, which speeds up the transfer by using multiple connections.
- <b>rsync</b>: This is the command to synchronize files and directories between a local and a remote location.
- <b>-r</b>: This flag tells rsync to perform a recursive copy of the entire directory tree.
- <b>-n</b>: This flag performs a "dry run," which means that the synchronization will be simulated, and no actual data will be transferred. This is useful to preview what would happen if the command were executed without actually making any changes.
- <b>-x</b>: This flag excludes files and directories that match any of the specified patterns using regular expressions. 
- <b>local_dir</b> C:\nodd\test: This is the local directory that will be synchronized.
- <b>cloud_dir</b> gs://nmfs_odp_pifsc/PIFSC/ESD/ARP/test: This is the Google Cloud Storage bucket and destination path where the data will be synchronized.

The <b>-x </b>excluded patterns in detail in this case are: 
- <b>(^.*(?<!\.JPG)$)</b>
- - Matches any files that do not end with the ".JPG" extension. 
- <b>(.*_archive.*|.*_YEAR.*|.*ISLAND.*|.*SITE-ID.*|.*SITE_PHOTOS.*|.*uncorrected.*|.*MISC.*|.*DARK.*|.*Products.*)</b>
- - Matches any files or directories that contain any of the specified strings.

</details>

### Simple NODD Download Script Example
```
gsutil -m rsync -r gs://<source_bucket_name>/<source_folder_path> <destination_folder_path>
```

### NODD Details
NODD
- https://www.noaa.gov/information-technology/open-data-dissemination

PIFSC NODD
- GSUtil URL
- - gs://nmfs_odp_pifsc
- Bucket API
- - https://www.googleapis.com/storage/v1/b/nmfs_odp_pifsc/o

Google Cloud SDK Docs
- https://cloud.google.com/sdk/docs
- https://cloud.google.com/storage/docs/discover-object-storage-gsutil

----------
#### Disclaimer
This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project content is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

## License
See the [LICENSE.md](./LICENSE.md) for details