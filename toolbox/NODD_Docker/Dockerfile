# Dockerfile
FROM google/cloud-sdk:latest

# Install gsutil
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install gsutil

# Copy gsutil configuration
COPY .boto /root/.boto

# Set the entrypoint to bash for running commands
ENTRYPOINT ["bash"]
