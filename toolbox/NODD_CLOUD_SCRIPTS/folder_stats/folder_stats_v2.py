import os
import sqlite3
import pandas as pd
from google.cloud import storage
import logging
import time

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_prefix TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to store metadata in the SQLite database in batches
def store_metadata(db_path, metadata_batch):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert metadata batch
    insert_query = '''INSERT INTO metadata (path, type, size, time_created, updated, md5Hash, mediaLink) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)'''
    cursor.executemany(insert_query, metadata_batch)
    
    conn.commit()
    conn.close()

# Function to update the progress in the database
def update_progress(db_path, last_prefix):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update progress table
    cursor.execute('DELETE FROM progress')
    cursor.execute('INSERT INTO progress (last_prefix) VALUES (?)', (last_prefix,))
    
    conn.commit()
    conn.close()

# Function to get the last processed prefix from the database
def get_last_prefix(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT last_prefix FROM progress ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Function to gather metadata from Google Cloud Storage using the API
def gather_metadata(bucket_name, prefix, db_path, batch_size=100, retry_limit=3):
    client = storage.Client()
    blobs = client.list_blobs(bucket_name, prefix=prefix, delimiter='/')

    metadata_batch = []
    folder_paths = set()

    print("Fetching blobs...")
    for blob in blobs:
        print(f"Found blob: {blob.name}")
        if blob.name.endswith('/'):
            folder_paths.add(blob.name)
            metadata_batch.append((blob.name, 'folder', 0, blob.time_created.isoformat() if blob.time_created else None, blob.updated.isoformat() if blob.updated else None, None, None))
        else:
            folder_path = '/'.join(blob.name.split('/')[:-1]) + '/'
            folder_paths.add(folder_path)
            metadata_batch.append((folder_path, 'file', blob.size, blob.time_created.isoformat() if blob.time_created else None, blob.updated.isoformat() if blob.updated else None, blob.md5_hash, blob.media_link))

        # Commit metadata in batches
        if len(metadata_batch) >= batch_size:
            store_metadata(db_path, metadata_batch)
            metadata_batch = []

    # Commit any remaining metadata
    if metadata_batch:
        store_metadata(db_path, metadata_batch)

    print("Fetching subfolders...")
    for subfolder in blobs.prefixes:
        retries = 0
        while retries < retry_limit:
            try:
                gather_metadata(bucket_name, subfolder, db_path, batch_size)
                break
            except Exception as e:
                retries += 1
                print(f"Error gathering metadata for {subfolder}: {e}. Retrying ({retries}/{retry_limit})...")
                time.sleep(5)
        if retries == retry_limit:
            print(f"Failed to gather metadata for {subfolder} after {retry_limit} attempts.")

        # Update progress
        update_progress(db_path, subfolder)

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

    last_prefix = get_last_prefix(db_path)
    if last_prefix:
        print(f"Resuming from last processed prefix: {last_prefix}")
        prefix = last_prefix

    print("Gathering metadata from Google Cloud Storage...")
    try:
        gather_metadata(bucket_name, prefix, db_path)
    except Exception as e:
        print(f"An error occurred while gathering metadata: {e}")
        return
    
    print("Metadata gathering completed and stored in database.")

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