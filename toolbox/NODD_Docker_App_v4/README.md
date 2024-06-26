# NODD Docker App v04
NODD Google Cloud Web App Storage Management Tool. Lets users have easy interface to common data tasks. 

<img src="./docs/s01.png" >

## Features
- Scan Bucket and Gather a List of folders
- Fetch Metadata (file size,file hash, file link,  file name) & Generate Stats (folder size and file counts)

## Other Screenshots
<img src="./docs/s02.png" >

## Setup
### Add Credentials (either boto or adc or both)
## Example '.boto' File
```
[Credentials]
gs_access_key_id =YOUR_KEY_ID_HERE
gs_secret_access_key  YOUR_KEY_HERE
```
- use existing '.boto' crednetial file like this example
  - found under: "C:\Users\Firstname.Lastname\AppData\Roaming\gcloud\legacy_credentials\your.email@noaa.gov\"
  - or found under: "config\legacy_credentials\your.email@noaa.gov\"
- or create a new boto file with HMAC keys
  - Under google cloud storage settings > Interoperability tab > at bottom "Create a Key"

## Exmaple application_default_credentials json file (adc.json)
```
{
  "account": "",
  "client_id": "placeholder.apps.googleusercontent.com",
  "client_secret": "placeholder",
  "refresh_token": "placeholder",
  "type": "authorized_user",
  "universe_domain": "googleapis.com"
}
```
### Add Dockerfile
```
# Dockerfile
# Use the Google Cloud SDK as the base image
FROM google/cloud-sdk:latest

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Install Python and required packages
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Copy the .boto configuration file
COPY ./credentials/.boto /root/.boto
COPY ./credentials/.boto /root/.config/gcloud/.boto
COPY ./credentials/adc.json /root/.config/gcloud/application_default_credentials.json
# Expose the port Streamlit will run on
EXPOSE 8501

# Default command to run the Streamlit app
ENTRYPOINT ["streamlit", "run", "nodd_upload_tool.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
### Compose File
```
version: '3.8'
services:
  nodd-app:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./local_directory:/local_directory
    ports:
      - "8501:8501"
```
### requirements.txt
```
streamlit
pandas
google-cloud-storage
google-auth-httplib2
matplotlib
```
### Then Run
``
docker-compose up --build
``
### Go to app
```
http://localhost:8501/
```
