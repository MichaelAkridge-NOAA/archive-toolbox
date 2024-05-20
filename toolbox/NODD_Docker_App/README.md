# NODD Docker App Example
<img src="https://github.com/MichaelAkridge-NOAA/archive-toolbox/blob/5a99c372b3dd144f6699f19e2158b1e60ed807d3/_docs/icons/nodd_docker_app_01.png" >

### Add Credentials
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


### Add Dockerfile
```
# Dockerfile
FROM google/cloud-sdk:latest

# Set the working directory
WORKDIR /app

# Copy the application files
COPY ./ ./

# Install Python and required packages
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install -r requirements.txt

# Install gsutil
RUN pip3 install gsutil

# Copy gsutil configuration
COPY .boto /root/.boto

# Expose the port Streamlit will run on
EXPOSE 8501

# Set the entrypoint to run the Streamlit app
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
      - ./local-dir:/local_directory
    ports:
      - "8501:8501"
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/root/.boto
```
### requirements.txt
```
streamlit
google-cloud-storage
google-auth-httplib2
gsutil
```
### Then Run
``
docker-compose up --build
``
### Go to app
```
http://localhost:8501/
```
<img src="https://github.com/MichaelAkridge-NOAA/archive-toolbox/blob/5a99c372b3dd144f6699f19e2158b1e60ed807d3/_docs/icons/nodd_docker_app_01.png" >
<img src="https://github.com/MichaelAkridge-NOAA/archive-toolbox/blob/5a99c372b3dd144f6699f19e2158b1e60ed807d3/_docs/icons/nodd_docker_app_02.png" >
