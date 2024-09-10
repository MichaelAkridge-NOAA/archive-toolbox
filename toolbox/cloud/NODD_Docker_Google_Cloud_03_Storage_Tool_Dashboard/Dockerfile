# Dockerfile
FROM google/cloud-sdk:latest

WORKDIR /app

# Copy application files
COPY ./ ./

# Install Python and required packages
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install -r requirements.txt

# Expose the port Streamlit will run on
EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "nodd_upload_tool.py", "--server.port=8501", "--server.address=0.0.0.0"]