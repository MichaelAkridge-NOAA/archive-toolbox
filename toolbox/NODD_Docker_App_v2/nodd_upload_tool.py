import streamlit as st
import os
import subprocess

def get_folder_size(bucket_name, folder_path):
    try:
        result = subprocess.run(
            ["gsutil", "du", "-s", f"gs://{bucket_name}/{folder_path}"],
            check=True,
            text=True,
            capture_output=True
        )
        # The output is expected to be in the format: "SIZE  gs://bucket_name/folder_path"
        size_str = result.stdout.split()[0]
        total_size_bytes = int(size_str)
        total_size_gb = total_size_bytes / (1024 ** 3)  # Convert bytes to gigabytes
        return total_size_gb
    except subprocess.CalledProcessError as e:
        raise Exception(f"gsutil command failed: {e.stderr}")

def list_folders(bucket_name, prefix):
    try:
        result = subprocess.run(
            ["gsutil", "ls", "-r", f"gs://{bucket_name}/{prefix}"],
            check=True,
            text=True,
            capture_output=True
        )
        # The output includes all files and folders; filter out only the folders
        all_paths = result.stdout.splitlines()
        folders = set()
        prefix_len = len(f"gs://{bucket_name}/{prefix}")
        for path in all_paths:
            if path.endswith('/'):
                folder_path = path[prefix_len:].strip('/')
                folder_name = folder_path.split('/')[0]
                if folder_name:
                    folders.add(folder_name)
        return sorted(folders)
    except subprocess.CalledProcessError as e:
        raise Exception(f"gsutil command failed: {e.stderr}")

def parse_bucket_and_path(bucket_and_path):
    parts = bucket_and_path.split('/', 1)
    if len(parts) != 2:
        raise ValueError("Input must be in the format 'bucket_name/folder_path'")
    return parts[0], parts[1]

def upload_file():
    st.subheader("Upload File to Google Cloud Storage")
    bucket_and_path = st.text_input("Enter the bucket name and folder path for file upload (e.g., 'nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management')")
    if bucket_and_path:
        try:
            bucket_name, folder_path = parse_bucket_and_path(bucket_and_path)
        except ValueError as e:
            st.error(e)
            return

        uploaded_file = st.file_uploader("Choose a file")
        if uploaded_file is not None:
            local_file_path = os.path.join("/local_directory", uploaded_file.name)
            with open(local_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File uploaded successfully")

            try:
                result = subprocess.run(
                    ["gsutil", "-m", "rsync", "-r", "/local_directory", f"gs://{bucket_name}/{folder_path}"],
                    check=True,
                    text=True,
                    capture_output=True
                )
                st.success("File synced to Google Cloud Storage successfully")
                st.text(result.stdout)
            except subprocess.CalledProcessError as e:
                st.error("An error occurred while syncing the file to Google Cloud Storage")
                st.text(e.stderr)

def get_size():
    st.subheader("Get Folder Size in Google Cloud Storage")
    bucket_and_path_for_size = st.text_input("Enter the bucket name and folder path for size calculation (e.g., 'nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management')")
    if bucket_and_path_for_size:
        try:
            bucket_name_for_size, folder_path_for_size = parse_bucket_and_path(bucket_and_path_for_size)
        except ValueError as e:
            st.error(e)
            return

        if st.button("Get Folder Size"):
            try:
                total_size_gb = get_folder_size(bucket_name_for_size, folder_path_for_size)
                st.success(f"Total size of the folder: {total_size_gb:.2f} GB")
            except Exception as e:
                st.error(f"An error occurred: {e}")

def list_folders_ui():
    st.subheader("List Folders in Google Cloud Storage")
    bucket_and_path_for_listing = st.text_input("Enter the bucket name and prefix to list folders (e.g., 'nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management')")
    if bucket_and_path_for_listing:
        try:
            bucket_name_for_listing, prefix_for_listing = parse_bucket_and_path(bucket_and_path_for_listing)
        except ValueError as e:
            st.error(e)
            return

        if st.button("List Folders"):
            try:
                folders = list_folders(bucket_name_for_listing, prefix_for_listing)
                if folders:
                    st.write("Folders:")
                    for folder in folders:
                        st.write(folder)
                else:
                    st.write("No folders found.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

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

    tab1, tab2, tab3 = st.tabs(["📤 Upload File", "📏 Get Folder Size", "📂 List Folders"])

    with tab1:
        upload_file()
    with tab2:
        get_size()
    with tab3:
        list_folders_ui()

if __name__ == "__main__":
    main()

