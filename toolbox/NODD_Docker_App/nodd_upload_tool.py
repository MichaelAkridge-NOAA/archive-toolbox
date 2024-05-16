import streamlit as st
import os
import subprocess

def main():
    st.title("NODD Upload Tool")

    # File uploader
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        # Save the file to the local directory
        local_file_path = os.path.join("/local_directory", uploaded_file.name)
        with open(local_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File uploaded successfully")

        # Run the gsutil rsync command
        try:
            result = subprocess.run(
                ["gsutil", "-m", "rsync", "-r", "/local_directory", "gs://nmfs_odp_pifsc/PIFSC/ESD/ARP/data_management/data"],
                check=True,
                text=True,
                capture_output=True
            )
            st.success("File synced to Google Cloud Storage successfully")
            st.text(result.stdout)
        except subprocess.CalledProcessError as e:
            st.error("An error occurred while syncing the file to Google Cloud Storage")
            st.text(e.stderr)

if __name__ == "__main__":
    main()

