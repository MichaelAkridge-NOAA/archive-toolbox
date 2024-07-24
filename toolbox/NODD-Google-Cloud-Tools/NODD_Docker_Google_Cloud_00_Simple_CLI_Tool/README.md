# NODD Docker Example
### Credentials
- you can use either a .json file
- or legacy '.boto' crednetial file like this example
  - found under: C:\Users\Firstname.Lastname\AppData\Roaming\gcloud\legacy_credentials\your.email@noaa.gov\
### Dockerfile
```
# Dockerfile
FROM google/cloud-sdk:latest

# Install gsutil
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install gsutil

# Copy gsutil configuration
COPY .boto /root/.boto

# Set the entrypoint to bash for running commands
ENTRYPOINT ["bash"]
```
### Compose File
```
services:
  gsutil:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./local_dir:/data
    entrypoint: [ "gsutil", "-m", "rsync", "-r", "/data", "gs://nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management/data" ]
```

### Then Run
``
docker-compose up --build
``

<img align="right" src="https://github.com/MichaelAkridge-NOAA/archive-toolbox/blob/dd79d27ddd7792cf2f6049bd94ef4976e246698a/_docs/icons/docker_nodd_s1.png" >
