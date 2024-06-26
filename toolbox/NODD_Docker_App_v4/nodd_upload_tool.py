import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import sqlite3
import subprocess
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from threading import Thread, Event
from google.cloud import storage

# Set the project ID as an environment variable
os.environ['GOOGLE_CLOUD_PROJECT'] = 'your-project-id'

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

shutdown_event = Event()

def exponential_backoff_retry(func, max_retries=5, initial_delay=1, backoff_factor=2):
    retries = 0
    delay = initial_delay
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            logging.error(f"Error: {e}, retrying in {delay} seconds...")
            time.sleep(delay)
            retries += 1
            delay *= backoff_factor
    raise Exception(f"Failed after {max_retries} retries")

def init_db(db_path):
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    conn = sqlite3.connect(db_path, timeout=30)  # Increased timeout
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
            last_processed_folder TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path TEXT,
            processed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def list_folders_with_gsutil(bucket_name, prefix, db_path):
    gsutil_command = f"gsutil ls -d gs://{bucket_name}/{prefix}*"
    result = subprocess.run(gsutil_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("Error running gsutil command: %s", result.stderr)
        return

    unique_prefixes = result.stdout.splitlines()
    if not unique_prefixes:
        logging.warning("No folders found. Please check the bucket name and prefix.")

    formatted_prefixes = [prefix.replace(f"gs://{bucket_name}/", "") for prefix in unique_prefixes]

    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.executemany('INSERT INTO folders (folder_path) VALUES (?)', [(prefix,) for prefix in formatted_prefixes])
    conn.commit()
    conn.close()
    logging.info(f"Inserted {len(formatted_prefixes)} folders into the database.")

def store_metadata(db_path, metadata_batch, retry_limit=5):
    conn = None
    retries = 0
    while retries < retry_limit:
        try:
            conn = sqlite3.connect(db_path, timeout=30)  # Increased timeout
            cursor = conn.cursor()
            insert_query = '''INSERT INTO metadata (path, type, size, time_created, updated, md5Hash, mediaLink) 
                              VALUES (?, ?, ?, ?, ?, ?, ?)'''
            cursor.executemany(insert_query, metadata_batch)
            conn.commit()
            logging.info(f"Stored {len(metadata_batch)} metadata records in the database.")
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                retries += 1
                time.sleep(2)  # Wait before retrying
            else:
                raise
        finally:
            if conn:
                conn.close()
    if retries == retry_limit:
        logging.error("Failed to write to database after %d attempts due to database lock.", retry_limit)
        raise sqlite3.OperationalError("Database is locked after multiple retries")

def update_progress(db_path, last_processed_folder):
    conn = sqlite3.connect(db_path, timeout=30)  # Increased timeout
    cursor = conn.cursor()
    cursor.execute('DELETE FROM progress')
    cursor.execute('INSERT INTO progress (last_processed_folder, timestamp) VALUES (?, ?)', (last_processed_folder, time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_last_processed_folder(db_path):
    conn = sqlite3.connect(db_path, timeout=30)  # Increased timeout
    cursor = conn.cursor()
    cursor.execute('SELECT last_processed_folder FROM progress ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def db_writer(db_path, q):
    while True:
        try:
            batch = q.get(timeout=10)  # Timeout to periodically check for termination signal
        except queue.Empty:
            if shutdown_event.is_set():
                break
            continue
        if batch is None:
            break
        logging.info(f"Processing batch of {len(batch)} metadata records.")
        store_metadata(db_path, batch)
        q.task_done()
    logging.info("db_writer thread exiting, no more batches to process.")

def gather_metadata_with_retry(bucket_name, folder, db_path, batch_size=11000, retry_limit=3, q=None):
    def fetch_blobs():
        client = storage.Client()
        return client.list_blobs(bucket_name, prefix=folder, delimiter='/')
    
    blobs = exponential_backoff_retry(fetch_blobs, max_retries=retry_limit)

    metadata_batch = []
    logging.info("Fetching blobs for folder: %s", folder)
    count = 0
    for blob in blobs:
        if shutdown_event.is_set():
            logging.info("Shutdown event set, exiting gather_metadata")
            break
        
        count += 1
        if blob.name.endswith('/'):
            metadata_batch.append((blob.name, 'folder', 0, blob.time_created.isoformat() if blob.time_created else None, blob.updated.isoformat() if blob.updated else None, None, None))
        else:
            folder_path = '/'.join(blob.name.split('/')[:-1]) + '/'
            metadata_batch.append((folder_path, 'file', blob.size, blob.time_created.isoformat() if blob.time_created else None, blob.updated.isoformat() if blob.updated else None, blob.md5_hash, blob.media_link))

        if len(metadata_batch) >= batch_size:
            q.put(metadata_batch)
            logging.info(f"Queued {len(metadata_batch)} metadata records for folder: {folder}")
            metadata_batch = []

    if metadata_batch:
        q.put(metadata_batch)
        logging.info(f"Queued {len(metadata_batch)} metadata records for folder: {folder}")

    logging.info("Completed fetching %d blobs for folder: %s", count, folder)
    update_folder_status(db_path, folder, 1)

def update_folder_status(db_path, folder, status):
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.execute('UPDATE folders SET processed = ? WHERE folder_path = ?', (status, folder))
    conn.commit()
    conn.close()

def get_unprocessed_folders(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.execute('SELECT folder_path FROM folders WHERE processed = 0')
    folders = cursor.fetchall()
    conn.close()
    return [folder[0] for folder in folders]

def get_counts_and_sizes(db_path):
    conn = sqlite3.connect(db_path, timeout=30)  # Increased timeout
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

def monitor_queue(q):
    while True:
        size = q.qsize()
        logging.info(f"Queue size: {size}")
        if size == 0:
            logging.info("Queue is empty.")
            break
        if shutdown_event.is_set():
            break
        time.sleep(5)  # Adjust the sleep time as needed

def data_dashboard():
    bucket_name = ""
    prefix = ""

    st.subheader("NODD Google Cloud Storage Dashboard")
    bucket_and_path_for_dashboard = st.text_input("Enter the bucket name and prefix to display data (e.g., 'nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management')")

    if bucket_and_path_for_dashboard:
        try:
            bucket_name, prefix = parse_bucket_and_path(bucket_and_path_for_dashboard)
        except ValueError as e:
            st.error(str(e))
            return

    if st.button('List Folders'):
        if not bucket_and_path_for_dashboard:
            st.error("Please enter a valid bucket name and prefix.")
            return

        db_path = "/local_directory/metadata.db"  # Save metadata.db to the local directory
        init_db(db_path)

        st.write("Listing all folders in the specified bucket and prefix...")
        list_folders_with_gsutil(bucket_name, prefix, db_path)

        # Validate folders in the database
        conn = sqlite3.connect(db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM folders')
        folder_count = cursor.fetchone()[0]
        conn.close()
        st.write(f"Total folders found and stored in the database: {folder_count}")

        st.write("Folder listing completed.")

    if st.button('Fetch Metadata'):
        if not bucket_and_path_for_dashboard:
            st.error("Please enter a valid bucket name and prefix.")
            return

        db_path = "/local_directory/metadata.db"  # Save metadata.db to the local directory
        init_db(db_path)
        last_processed_folder = get_last_processed_folder(db_path)
        if last_processed_folder:
            st.write(f"Resuming from last processed folder: {last_processed_folder}")

        st.write("Gathering metadata from Google Cloud Storage...")

        q = queue.Queue()
        writer_thread = Thread(target=db_writer, args=(db_path, q))
        writer_thread.start()

        monitor_thread = Thread(target=monitor_queue, args=(q,))
        monitor_thread.start()

        folders = get_unprocessed_folders(db_path)
        for folder in folders:
            if shutdown_event.is_set():
                break
            gather_metadata_with_retry(bucket_name, folder, db_path, q=q)

        q.put(None)
        writer_thread.join()
        monitor_thread.join()

        st.write("Metadata gathering completed and stored in database.")

        # Validate record count in the database
        conn = sqlite3.connect(db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM metadata')
        record_count = cursor.fetchone()[0]
        conn.close()
        st.write(f"Total records in the database: {record_count}")

        if record_count == 0:
            st.error("No metadata records found in the database.")
            return

        result = get_counts_and_sizes(db_path)
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
        csv_path = '/local_directory/folder_stats.csv'  # Save folder_stats.csv to the local directory
        df.to_csv(csv_path, index=False)
        st.write("Statistics saved to folder_stats.csv")

        st.subheader("Metadata Summary")
        st.dataframe(df)
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='folder_stats.csv',
            mime='text/csv',
        )

def parse_bucket_and_path(bucket_and_path):
    parts = bucket_and_path.split('/', 1)
    if len(parts) != 2:
        raise ValueError("Input must be in the format 'bucket_name/folder_path'")
    return parts[0], parts[1]

def main():
    st.markdown("""
        <style>
        div[class*="stTabs"] button div[data-testid="stMarkdownContainer"] p {
            font-size: 24px;
        }
        </style>
    """, unsafe_allow_html=True)
    with st.sidebar:
        st.title("NODD Google Cloud Storage Management Tool")
        st.write("""
        Contact: Michael.Akridge@NOAA.Gov
        For more information:
        - Visit the GitHub repository: [PIFSC ESD/ARP Archive Toolbox](https://github.com/MichaelAkridge-NOAA/archive-toolbox)
        - View Google Cloud Bucket: [NMFS-PIFSC GC Bucket](https://console.cloud.google.com/storage/browser/nmfs_odp_pifsc)
        """)
    st.title("NODD Google Cloud Tool")
    data_dashboard()

if __name__ == "__main__":
    main()

