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

# Expose the port Streamlit will run on
EXPOSE 8501

# Default command to run the Streamlit app
ENTRYPOINT ["streamlit", "run", "nodd_upload_tool.py", "--server.port=8501", "--server.address=0.0.0.0"]