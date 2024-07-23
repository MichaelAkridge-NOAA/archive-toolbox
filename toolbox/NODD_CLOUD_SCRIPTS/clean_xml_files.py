import os
import re
import shutil
from google.cloud import storage
import logging

# Set the Google Cloud Project ID
os.environ["GOOGLE_CLOUD_PROJECT"] = "YOUR_PROJECT_ID"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_invalid_characters(xml_content):
    # Remove all non-printable characters except for newline, carriage return, and tab
    cleaned_content = re.sub(r'[^\x20-\x7E\x0A\x0D]', '', xml_content)
    return cleaned_content

def clean_xml_files_in_bucket(bucket_name, prefix, temp_folder):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = client.list_blobs(bucket_name, prefix=prefix)

    # Ensure the temporary folder exists
    os.makedirs(temp_folder, exist_ok=True)

    for blob in blobs:
        if blob.name.endswith(".xml"):
            logging.info(f"Processing file: {blob.name}")

            # Define local file path
            local_file_path = os.path.join(temp_folder, os.path.basename(blob.name))
            
            # Download the XML file to the temporary folder
            blob.download_to_filename(local_file_path)

            # Read the downloaded XML file
            with open(local_file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()

            # Clean the content
            cleaned_content = remove_invalid_characters(xml_content)

            # Write the cleaned content back to the local file
            with open(local_file_path, 'w', encoding='utf-8') as file:
                file.write(cleaned_content)

            # Upload the cleaned content back to the same blob
            blob.upload_from_filename(local_file_path)
            logging.info(f"Cleaned and updated file: {blob.name}")

    # Cleanup: remove the temporary folder and its contents
    shutil.rmtree(temp_folder)
    logging.info("Temporary files removed.")

# Main function to run the script
def main():
    bucket_and_prefix = input("Enter the bucket name and prefix (e.g., 'my_bucket/my_prefix/'): ")
    
    try:
        bucket_name, prefix = bucket_and_prefix.split('/', 1)
    except ValueError:
        logging.error("Input must be in the format 'bucket_name/prefix'")
        return

    temp_folder = 'temp_xml_files'

    logging.info("Starting to clean XML files in the bucket...")
    try:
        clean_xml_files_in_bucket(bucket_name, prefix, temp_folder)
    except Exception as e:
        logging.error("An error occurred while cleaning XML files: %s", e)
        return
    
    logging.info("Cleaning process completed.")

if __name__ == "__main__":
    main()