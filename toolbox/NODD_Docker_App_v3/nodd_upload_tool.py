import streamlit as st
import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

# Cache the results of the functions to prevent re-execution
@st.cache_data
def get_folder_stats(bucket_name, folder_path):
    try:
        result = subprocess.run(
            ["gsutil", "ls", "-l", f"gs://{bucket_name}/{folder_path}/**"],
            check=True,
            text=True,
            capture_output=True
        )
        total_size_bytes = 0
        file_count = 0
        unique_files = set()
        for line in result.stdout.splitlines():
            if line:
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    size_bytes = int(parts[0])
                    file_path = parts[-1]
                    if file_path not in unique_files:
                        unique_files.add(file_path)
                        total_size_bytes += size_bytes
                        file_count += 1
        total_size_gb = total_size_bytes / (1024 ** 3)
        return total_size_gb, file_count
    except subprocess.CalledProcessError as e:
        raise Exception(f"gsutil command failed: {e.stderr}")

@st.cache_data
def list_folders_with_stats(bucket_name, prefix):
    try:
        result = subprocess.run(
            ["gsutil", "ls", "-d", f"gs://{bucket_name}/{prefix}**"],
            check=True,
            text=True,
            capture_output=True
        )
        all_paths = result.stdout.splitlines()
        folder_stats = []
        for path in all_paths:
            if path.endswith('/'):
                folder_path = path.split(f"gs://{bucket_name}/")[1].strip('/')
                folder_size, file_count = get_folder_stats(bucket_name, folder_path)
                folder_stats.append((folder_path, folder_size, file_count))
        return folder_stats
    except subprocess.CalledProcessError as e:
        raise Exception(f"gsutil command failed: {e.stderr}")

def parse_bucket_and_path(bucket_and_path):
    parts = bucket_and_path.split('/', 1)
    if len(parts) != 2:
        raise ValueError("Input must be in the format 'bucket_name/folder_path'")
    return parts[0], parts[1]

def data_dashboard():
    st.subheader("NODD Google Cloud Storage Dashboard")
    
    bucket_and_path_for_dashboard = st.text_input("Enter the bucket name and prefix to display data (e.g., 'nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management')")
    
    if bucket_and_path_for_dashboard:
        try:
            bucket_name, prefix = parse_bucket_and_path(bucket_and_path_for_dashboard)
        except ValueError as e:
            st.error(e)
            return
        
        if st.button("Load Dashboard"):
            st.write("**Folder Statistics:**")
            try:
                folder_stats = list_folders_with_stats(bucket_name, prefix)
                if not folder_stats:
                    st.write("No folders found.")
                    return

                folder_names = [stat[0] for stat in folder_stats]
                folder_sizes = [stat[1] for stat in folder_stats]
                file_counts = [stat[2] for stat in folder_stats]
                
                stats_df = pd.DataFrame({
                    "Folder": folder_names,
                    "Size (GB)": folder_sizes,
                    "File Count": file_counts
                })
                st.table(stats_df)
            except Exception as e:
                st.error(f"An error occurred: {e}")
                return

            st.write("**Folder Sizes Distribution:**")
            fig, ax = plt.subplots()
            ax.barh(folder_names, folder_sizes, color='skyblue')
            ax.set_xlabel('Size (GB)')
            ax.set_title('Folder Sizes in Google Cloud Storage')
            st.pyplot(fig)

            st.write("**File Counts Distribution:**")
            fig, ax = plt.subplots()
            ax.barh(folder_names, file_counts, color='lightgreen')
            ax.set_xlabel('Number of Files')
            ax.set_title('File Counts in Google Cloud Storage')
            st.pyplot(fig)

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
            st.success("File staged successfully. To continue with cloud upload, press Sync File")

            if st.button("Sync File"):
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
                total_size_gb, file_count = get_folder_stats(bucket_name_for_size, folder_path_for_size)
                st.success(f"Total size of the folder: {total_size_gb:.2f} GB")
                st.success(f"Total number of files: {file_count}")
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
                folders = list_folders_with_stats(bucket_name_for_listing, prefix_for_listing)
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

    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload File", "📏 Get Folder Size", "📂 List Folders", "📊 Data Dashboard"])

    with tab1:
        upload_file()
    with tab2:
        get_size()
    with tab3:
        list_folders_ui()
    with tab4:
        data_dashboard()

if __name__ == "__main__":
    main()
