import streamlit as st
import subprocess
from datetime import datetime
import os

# Function to handle file copying, adapted for Streamlit
def start_copy(source_paths, destination_path, log_path):
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    copy_results = []
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    for source_path in source_paths:
        if os.path.exists(source_path):
            source_folder_name = os.path.basename(os.path.normpath(source_path))
            log_filename = f"{source_folder_name}_{current_datetime}_copy.log"
            log_file_path = os.path.join(log_path, log_filename)

            # robocopy command
            #/mt: copying process by using multiple threads.This can speed up the copying process.Number can be specified (example: /mt:8 for 8 threads). If not specified a number, robocopy uses the default value.
            #/XX: Excludes extra files and directories (those on the destination but not in the source).
            #/z: Copies files in restartable mode, which can resume partially copied files if the copy process is interrupted.
            #/mir: Mirrors a directory tree. This option deletes files in the destination directory that are no longer present in the source directory.
            command = ["robocopy", source_path, os.path.join(destination_path, source_folder_name), "/mt", "/XX", "/z", "/mir", "/LOG:" + log_file_path]
            result = subprocess.run(command, capture_output=True, text=True)
            copy_results.append((source_path, result.returncode))
        else:
            copy_results.append((source_path, "Source path does not exist"))
    
    return copy_results

# Streamlit UI
st.title('Bulk Directory Copy Tool')

# Text area for source directories input
source_dirs_input = st.text_area("Enter the paths of source directories (one per line):", height=300)
source_paths = source_dirs_input.split('\n')  # Split input into a list by new lines

# Input for destination directory
destination_path = st.text_input("Enter Destination Directory Path")

# Input for log directory
log_path = st.text_input("Enter Log Directory Path")

# Start copy process
if st.button('Start Copy'):
    if source_paths and destination_path and log_path:
        copy_results = start_copy(source_paths, destination_path, log_path)
        for source, result in copy_results:
            if isinstance(result, int):  # Check if result is a return code
                if result == 0 or result == 1:
                    st.success(f"Successfully copied {source}")
                else:
                    st.error(f"Failed to copy {source} with return code {result}")
            else:
                st.error(result)
    else:
        st.error("Please enter all required fields")
