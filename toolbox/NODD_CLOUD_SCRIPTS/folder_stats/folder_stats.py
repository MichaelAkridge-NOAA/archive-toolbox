import os
import sqlite3
import pandas as pd
from google.cloud import storage
import logging

# Set the Google Cloud Project ID
os.environ["GOOGLE_CLOUD_PROJECT"] = "YOUR_PROJECT_ID"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to initialize the SQLite database
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY,
            path TEXT,
            type TEXT,
            size INTEGER,
            time_created TEXT,
            updated TEXT,
            md5Hash TEXT,
            mediaLink TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to store metadata in the SQLite database, replacing existing records
def store_metadata(db_path, metadata):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Truncate the metadata table
    cursor.execute('DELETE FROM metadata')
    
    # Insert new metadata
    insert_query = '''INSERT INTO metadata (path, type, size, time_created, updated, md5Hash, mediaLink) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)'''
    cursor.executemany(insert_query, metadata)
    
    conn.commit()
    conn.close()

    # Print insert statements for the metadata
    #for item in metadata:
        #print("INSERT INTO metadata (path, type, size, time_created, updated, md5Hash, mediaLink) VALUES ('{}', '{}', {}, '{}', '{}', '{}', '{}');".format(*item))

# Function to gather metadata from Google Cloud Storage using the API
def gather_metadata(bucket_name, prefix):
    client = storage.Client()
    blobs = client.list_blobs(bucket_name, prefix=prefix, delimiter='/')

    metadata = []
    folder_paths = set()

    print("Fetching blobs...")
    for blob in blobs:
        print(f"Found blob: {blob.name}")
        if blob.name.endswith('/'):
            folder_paths.add(blob.name)
            metadata.append((blob.name, 'folder', 0, blob.time_created.isoformat() if blob.time_created else None, blob.updated.isoformat() if blob.updated else None, None, None))
        else:
            folder_path = '/'.join(blob.name.split('/')[:-1]) + '/'
            folder_paths.add(folder_path)
            metadata.append((folder_path, 'file', blob.size, blob.time_created.isoformat() if blob.time_created else None, blob.updated.isoformat() if blob.updated else None, blob.md5_hash, blob.media_link))

    print("Fetching subfolders...")
    for subfolder in blobs.prefixes:
        metadata.extend(gather_metadata(bucket_name, subfolder))

    return metadata

# Function to get counts and sizes from the database
def get_counts_and_sizes(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            path,
            SUM(CASE WHEN type = 'file' THEN size ELSE 0 END) AS total_size,
            COUNT(CASE WHEN type = 'file' THEN 1 END) AS file_count,
            COUNT(DISTINCT CASE WHEN type = 'folder' THEN path ELSE NULL END) AS folder_count,
            MIN(time_created) AS earliest_time_created,
            MAX(updated) AS latest_updated
        FROM metadata
        GROUP BY path
    ''')
    result = cursor.fetchall()
    conn.close()
    return result

# Function to parse the bucket name and prefix from the input
def parse_bucket_and_prefix(bucket_and_prefix):
    parts = bucket_and_prefix.split('/', 1)
    if len(parts) != 2:
        raise ValueError("Input must be in the format 'bucket_name/prefix'")
    return parts[0], parts[1]

# Main function to run the script
def main():
    bucket_and_prefix = input("Enter the bucket name and prefix (e.g., 'nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management'): ")
    
    try:
        bucket_name, prefix = parse_bucket_and_prefix(bucket_and_prefix)
    except ValueError as e:
        print(e)
        return
    
    db_path = "metadata.db"
    init_db(db_path)

    print("Gathering metadata from Google Cloud Storage...")
    metadata = gather_metadata(bucket_name, prefix)
    print(f"Metadata gathering completed. Found {len(metadata)} items. Storing in database...")

    if not metadata:
        print("No metadata parsed.")
        return

    store_metadata(db_path, metadata)
    print("Metadata stored in database.")

    result = get_counts_and_sizes(db_path)
    print("Statistics calculated:")

    data = []
    for row in result:
        data.append({
            'Path': row[0],
            'Size (Bytes)': row[1],
            'File Count': row[2],
            'Folder Count': row[3],
            'Earliest Time Created': row[4],
            'Latest Updated': row[5]
        })

    df = pd.DataFrame(data)
    df["Size (GiB)"] = df["Size (Bytes)"] / (1024 ** 3)  # Convert bytes to GiB
    csv_path = 'folder_stats.csv'
    df.to_csv(csv_path, index=False)
    print(f"Statistics saved to {csv_path}")

if __name__ == "__main__":
    main()
