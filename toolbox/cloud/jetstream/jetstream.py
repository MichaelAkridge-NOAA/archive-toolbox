import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
# to get current date & time
from datetime import datetime
from gooey import Gooey, GooeyParser
try:
    import wx  # Gooey GUI backend
    WX_AVAILABLE = True
except Exception:
    WX_AVAILABLE = False
import google
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import logging
import time
import re
from typing import List, Dict, Optional
# Define the scopes that your application needs to access Google Cloud Storage
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

class UploadConfig:
    """Configuration class for upload patterns and settings."""
    
    def __init__(self):
        self.default_include_patterns = [
            r'^.*(?<!\.JPG)$',  # Everything except files ending with .JPG
            r'^.*\.(jpg|jpeg|png|tiff|tif|raw|cr2|nef|arw|dng)$',  # Image files
            r'^.*\.(mp4|mov|avi|mkv)$',  # Video files
            r'^.*\.(txt|csv|json|xml|log)$'  # Data files
        ]
        
        self.default_exclude_folders = [
            "_archive", "_YEAR", "ISLAND", "SITE-ID", "SITE_PHOTOS", 
            "Corrected", "corrected", "uncorrected", "MISC", "DARK", 
            "Products", "Thumbs.db", ".DS_Store", "__pycache__"
        ]
        
        self.default_exclude_patterns = [
            r'.*\.tmp$',  # Temporary files
            r'.*\.bak$',  # Backup files
            r'.*~$',      # Editor backup files
            r'.*\.pyc$',  # Python compiled files
        ]
    
    @classmethod
    def from_json_file(cls, filepath: str) -> 'UploadConfig':
        """Load configuration from JSON file."""
        config = cls()
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    config.default_include_patterns = data.get('include_patterns', config.default_include_patterns)
                    config.default_exclude_folders = data.get('exclude_folders', config.default_exclude_folders)
                    config.default_exclude_patterns = data.get('exclude_patterns', config.default_exclude_patterns)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Warning: Could not load config from {filepath}: {e}")
        return config
    
    def to_json_file(self, filepath: str):
        """Save configuration to JSON file."""
        data = {
            'include_patterns': self.default_include_patterns,
            'exclude_folders': self.default_exclude_folders,
            'exclude_patterns': self.default_exclude_patterns
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

class BucketPathManager:
    """Manages Google Cloud Storage bucket paths."""
    
    @staticmethod
    def validate_bucket_path(path: str) -> bool:
        """Validate bucket path format."""
        if not path:
            return False
        
        # Remove gs:// prefix if present
        if path.startswith('gs://'):
            path = path[5:]
        
        # Basic validation: should have at least bucket name
        parts = path.split('/')
        return len(parts) >= 1 and len(parts[0]) > 0
    
    @staticmethod
    def normalize_bucket_path(path: str) -> str:
        """Normalize bucket path to proper format."""
        if not path:
            return ""
        # Remove gs:// prefix if present
        if path.startswith('gs://'):
            path = path[5:]
        # Convert Windows backslashes to forward slashes if accidentally provided
        path = path.replace('\\', '/')
        # Remove leading/trailing slashes
        path = path.strip('/')
        # Return with gs:// prefix
        return f"gs://{path}"
    
    @staticmethod
    def get_common_bucket_paths() -> List[str]:
        """Return list of common NOAA bucket paths."""
        return [
            "nmfs_odp_pifsc/PIFSC/ESD/ARP"
        ]

def authenticate():
    """Authenticate with Google using the OAuth2 Web Application Flow"""
    # Set up the OAuth2 flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',  # Path to your client secret file
        scopes=SCOPES)

    # Start the OAuth2 flow and redirect the user to the Google sign-in page
    credentials = flow.run_local_server(port=0)

    # Save the credentials to a file (or database) for future use
    with open('credentials.json', 'w') as f:
        f.write(credentials.to_json())

    return credentials

def get_credentials():
    """Load the stored credentials or authenticate if they do not exist"""
    try:
        # Try to load the credentials from the file
        credentials = Credentials.from_authorized_user_file('credentials.json', SCOPES)
    except FileNotFoundError:
        # If the file does not exist, authenticate with Google
        credentials = authenticate()
    return credentials

def log_and_print(message):
    """Logs the message and also prints it to the console."""
    logging.info(message)
    print(message)

# Preflight verification helpers removed per request
    
def generate_gsutil_command(
    source_path: str, 
    dest_path: str, 
    include_patterns: List[str] = None,
    exclude_folders: List[str] = None,
    exclude_patterns: List[str] = None,
    dry_run: bool = False,
    threads: int = 12,
    enable_multi: bool = False,
    recursive: bool = True
) -> str:
    """
    Generate the gsutil command string based on the provided parameters.
    
    Args:
        source_path: Local source directory path
        dest_path: Destination bucket path (with gs:// prefix)
        include_patterns: List of regex patterns for files to include
        exclude_folders: List of folder names to exclude
        exclude_patterns: List of regex patterns for files to exclude
        dry_run: If True, performs a dry run without actual transfer
        threads: Number of parallel threads to use
        enable_multi: Enable multi-threading
        recursive: Perform recursive copy
    
    Returns:
        Complete gsutil command string
    """
    config = UploadConfig()
    
    # Use provided patterns or defaults
    if include_patterns is None:
        include_patterns = config.default_include_patterns
    if exclude_folders is None:
        exclude_folders = config.default_exclude_folders
    if exclude_patterns is None:
        exclude_patterns = config.default_exclude_patterns
    
    # Build exclude pattern from folders and patterns
    folder_patterns = [f'.*{folder}.*' for folder in exclude_folders]
    all_exclude_patterns = folder_patterns + exclude_patterns
    combined_exclude_pattern = '|'.join(all_exclude_patterns)
    
    # Build command flags
    dry_run_flag = "-n" if dry_run else ""
    threads_flag = f"-o GSUtil:parallel_thread_count={threads}" if threads else ""
    enable_multi_flag = "-m" if enable_multi else ""
    recursive_flag = "-r" if recursive else ""
    exclude_flag = f'-x "{combined_exclude_pattern}"' if combined_exclude_pattern else ""
    
    # Normalize and quote local source path for Windows compatibility
    if os.path.exists(source_path):
        normalized_source = Path(source_path).resolve().as_posix()
    else:
        normalized_source = source_path.replace('\\', '/')
    quoted_source = f'"{normalized_source}"'

    # Normalize and quote destination bucket path
    quoted_dest = f'"{dest_path}"'

    # Log normalized paths for debugging
    print(f"Normalized source path: {quoted_source}")
    print(f"Normalized destination path: {quoted_dest}")

    cmd_parts = [
        "gsutil",
        threads_flag,
        enable_multi_flag,
        "rsync",
        recursive_flag,
        dry_run_flag,
        exclude_flag,
        quoted_source,
        quoted_dest
    ]
    gsutil_command = ' '.join(filter(None, cmd_parts))
    return gsutil_command

def do_the_copy(
    source_path: str,
    dest_path: str, 
    log_path: str,
    include_patterns: List[str] = None,
    exclude_folders: List[str] = None,
    exclude_patterns: List[str] = None,
    dry_run: bool = False,
    threads: int = 12,
    enable_multi: bool = False,
    recursive: bool = True
) -> bool:
    """
    Run the gsutil command for copying files based on the provided parameters.
    
    Returns:
        bool: True if successful, False otherwise
    """    
    gsutil_command = generate_gsutil_command(
        source_path=source_path,
        dest_path=dest_path,
        include_patterns=include_patterns,
        exclude_folders=exclude_folders,
        exclude_patterns=exclude_patterns,
        dry_run=dry_run,
        threads=threads,
        enable_multi=enable_multi,
        recursive=recursive
    )
    
    print("Running Sync Script:")
    print("=" * 50)
    print(gsutil_command)
    print("=" * 50)
    
    # Run gsutil command and capture output
    start_time = time.time()
    try:
        process = subprocess.Popen(
            gsutil_command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        output, _ = process.communicate()
        elapsed_time = time.time() - start_time
        
        if process.returncode == 0:
            log_and_print('---- Copy Process Successful ----')
            log_and_print(f'Elapsed Time: {elapsed_time:.2f} seconds')
            log_and_print('Output:')
            log_and_print(output)
            return True
        else:
            log_and_print('---- Copy Process Failed ----')
            log_and_print(f'Elapsed Time: {elapsed_time:.2f} seconds')
            log_and_print('Error:')
            log_and_print(output)
            return False
            
    except Exception as e:
        log_and_print(f'---- Exception occurred during copy process ----')
        log_and_print(f'Error: {str(e)}')
        return False
        
def parse_args():
    """Parses command-line arguments for the GUI."""
    parser = GooeyParser(description='NOAA Jetstream — Cloud upload for Google Cloud Storage with custom patterns')

    # Main Options - Clean Layout
    main_group = parser.add_argument_group("Source & Destination")
    main_group.add_argument('--copy-from', dest='copy_from', required=True, widget='DirChooser', help='Select the local folder to upload')
    main_group.add_argument('--bucket-path', dest='bucket_path', required=True, widget='TextField', help='Google Cloud Storage bucket path (e.g., nmfs_odp_pifsc/PIFSC/ESD/ARP/Photoquadrat Imagery)')
    main_group.add_argument('--log-directory', dest='log_directory', required=True, widget='DirChooser', help='Folder to save transfer logs')

    transfer_group = parser.add_argument_group("Transfer Settings")
    transfer_group.add_argument('--dry-run', action='store_true', help='Preview transfer without copying files (safe test mode)')
    transfer_group.add_argument('--threads', type=int, default=12, widget='Slider', help='Number of parallel threads (1-24)', gooey_options={'min': 1, 'max': 24})
    transfer_group.add_argument('--enable-multi', action='store_true', default=True, help='Enable multi-threading for faster transfers')
    transfer_group.add_argument('--recursive-copy', action='store_true', default=True, help='Recursively copy all subfolders and files')
    transfer_group.add_argument('--print-command', action='store_true', help='Show the gsutil command that will be run (no transfer performed)')

    # Preflight checks UI removed

    # Advanced Tab: Save/Load Config and Pattern Options
    advanced_group = parser.add_argument_group("Advanced Options", gooey_options={"tab": "Advanced"})
    advanced_group.add_argument('--save-config', widget='FileSaver', help='Save current patterns to configuration file', gooey_options={'wildcard': 'JSON files (*.json)|*.json', 'default_file': 'gcs_upload_config.json'})
    advanced_group.add_argument('--load-config', widget='FileChooser', help='Load patterns from configuration file', gooey_options={'wildcard': 'JSON files (*.json)|*.json'})
    advanced_group.add_argument('--use-include-patterns', action='store_true', help='Enable custom include patterns (otherwise all files are included)')
    advanced_group.add_argument('--include-patterns', widget='Textarea', help='Include patterns (one regex per line)\nExample:\n^.*\\.(jpg|jpeg|png)$\n^.*\\.txt$', default='')
    advanced_group.add_argument('--use-exclude-folders', action='store_true', help='Enable folder exclusion')
    advanced_group.add_argument('--exclude-folders', widget='Textarea', help='Exclude folders (one name per line)\nExample:\n_archive\nThumbs\n.DS_Store', default='_archive\n_YEAR\nISLAND\nSITE-ID\nSITE_PHOTOS\nCorrected\ncorrected\nuncorrected\nMISC\nDARK\nProducts\nThumbs.db\n.DS_Store\n__pycache__')
    advanced_group.add_argument('--use-exclude-patterns', action='store_true', help='Enable pattern-based file exclusion')
    advanced_group.add_argument('--exclude-patterns', widget='Textarea', help='Exclude patterns (one regex per line)\nExample:\n.*\\.tmp$\n.*\\.bak$', default='.*\\.tmp$\n.*\\.bak$\n.*~$\n.*\\.pyc$')

    return parser.parse_args()

def parse_args_cli():
    """Parses command-line arguments for CLI mode (no GUI)."""
    parser = argparse.ArgumentParser(description='NOAA Jetstream (CLI mode)')
    parser.add_argument('--copy-from', dest='copy_from', required=True, help='Local folder to upload')
    parser.add_argument('--bucket-path', dest='bucket_path', required=True, help='Google Cloud Storage bucket path (gs://bucket/path or bucket/path)')
    parser.add_argument('--log-directory', dest='log_directory', required=True, help='Folder to save transfer logs')
    parser.add_argument('--dry-run', action='store_true', help='Preview transfer without copying files (safe test mode)')
    parser.add_argument('--threads', type=int, default=12, help='Number of parallel threads (1-24)')
    parser.add_argument('--enable-multi', action='store_true', default=True, help='Enable multi-threading for faster transfers')
    parser.add_argument('--recursive-copy', action='store_true', default=True, help='Recursively copy all subfolders and files')
    parser.add_argument('--print-command', action='store_true', help='Show the gsutil command that will be run (no transfer performed)')
    return parser.parse_args()

def parse_patterns_from_text(text: str) -> List[str]:
    """Parse patterns from textarea input, filtering out empty lines."""
    if not text:
        return []
    return [line.strip() for line in text.split('\n') if line.strip()]

@Gooey(
    program_name='NOAA Jetstream',
    default_size=(800, 900),
    image_dir='./_icons',
    navigation='TABBED',
    tabbed_groups=True,
    menu=[{
        'name': 'NOAA Jetstream',
        'items': [{
            'type': 'AboutDialog',
            'menuTitle': 'About',
            'name': 'NOAA Jetstream',
            'description': 'NOAA Jetstream — Cloud upload tool for Google Cloud',
            'version': '2.0',
            'copyright': '2024',
            'website': 'https://github.com/MichaelAkridge-NOAA/archive-toolbox',
            'developer': 'Michael Akridge'
        }]
    }],
    show_success_modal=True,
    show_failure_modal=True
)
def main_gui():
    # If GUI backend is missing, exit with instructions (avoid CLI fallback)
    if not WX_AVAILABLE:
        print("Gooey GUI requires wxPython, which is not installed.")
        print("Install it in your environment, then re-run this app.")
        print("Conda:  conda install -c conda-forge wxpython")
        print("Pip:    pip install -U wxPython")
        return
    """Main function to handle the upload process (GUI)."""
    args = parse_args()
    current_datetime = datetime.now().strftime("%m_%d_%Y_%H%M")
    # Debug received args from GUI
    print("Received arguments from UI:")
    print(f"  COPY_FROM: {getattr(args, 'copy_from', None)}")
    print(f"  BUCKET_PATH: {getattr(args, 'bucket_path', None)}")
    print(f"  LOG_DIRECTORY: {getattr(args, 'log_directory', None)}")

    def sanitize_local_path(p: str) -> str:
        if not p:
            return p
        p = p.strip().strip('"')
        # Avoid breaking drive roots like C:\
        if len(p) > 3:
            p = p.rstrip('\\/')
        return p

    # Start with provided args
    pathvalue1 = sanitize_local_path(args.copy_from)
    pathvalue2 = BucketPathManager.normalize_bucket_path(args.bucket_path) if args.bucket_path else ''
    pathvalue3 = sanitize_local_path(args.log_directory)

    # Build pattern controls from GUI toggles
    use_include = getattr(args, 'use_include_patterns', False)
    use_excl_dirs = getattr(args, 'use_exclude_folders', False)
    use_excl_patterns = getattr(args, 'use_exclude_patterns', False)

    include_patterns_list = parse_patterns_from_text(getattr(args, 'include_patterns', '')) if use_include else []
    exclude_folders_list = parse_patterns_from_text(getattr(args, 'exclude_folders', '')) if use_excl_dirs else []
    exclude_patterns_list = parse_patterns_from_text(getattr(args, 'exclude_patterns', '')) if use_excl_patterns else []

    # If required fields are missing, show clear errors (let user fill fields in GUI)
    if not pathvalue1 or not os.path.isdir(pathvalue1):
        print("Error: Please select a valid COPY_FROM directory in the GUI.")
        return
    if not pathvalue3 or not os.path.isdir(pathvalue3):
        print("Error: Please select a valid LOG_DIRECTORY in the GUI.")
        return
    if not pathvalue2:
        print("Error: Please enter a valid BUCKET_PATH in the GUI.")
        return
    LOG_FILENAME = current_datetime + "_jetstream_transfer.log"
    LOG_FILENAME_PATH = os.path.join(pathvalue3, LOG_FILENAME)
    logging.basicConfig(filename=LOG_FILENAME_PATH, level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')

    # All values present — proceed

    # Normalize and validate bucket path
    normalized_bucket = BucketPathManager.normalize_bucket_path(pathvalue2)
    if not BucketPathManager.validate_bucket_path(normalized_bucket):
        print("Error: Bucket path format is invalid.")
        return

    # Preflight verification removed

    if args.print_command:
        print("gsutil command:")
        print("    ")
        gsutil_command = generate_gsutil_command(
            source_path=pathvalue1,
            dest_path=normalized_bucket,
            include_patterns=include_patterns_list,
            exclude_folders=exclude_folders_list,
            exclude_patterns=exclude_patterns_list,
            dry_run=args.dry_run,
            threads=args.threads,
            enable_multi=args.enable_multi,
            recursive=args.recursive_copy
        )
        print(gsutil_command)
    else:
        do_the_copy(
            source_path=pathvalue1,
            dest_path=normalized_bucket,
            log_path=pathvalue3,
            include_patterns=include_patterns_list,
            exclude_folders=exclude_folders_list,
            exclude_patterns=exclude_patterns_list,
            dry_run=args.dry_run,
            threads=args.threads,
            enable_multi=args.enable_multi,
            recursive=args.recursive_copy
        )
        log_and_print('-------------------------------------------------')
        log_and_print('---- Copy Process Complete ----')

def cli_main():
    """Non-GUI CLI entrypoint with explicit flags."""
    args = parse_args_cli()
    current_datetime = datetime.now().strftime("%m_%d_%Y_%H%M")
    def sanitize_local_path(p: str) -> str:
        if not p:
            return p
        p = p.strip().strip('"')
        if len(p) > 3:
            p = p.rstrip('\\/')
        return p
    pathvalue1 = sanitize_local_path(args.copy_from)
    pathvalue2 = BucketPathManager.normalize_bucket_path(args.bucket_path)
    pathvalue3 = sanitize_local_path(args.log_directory)
    if not os.path.isdir(pathvalue1):
        print(f"Error: COPY_FROM is not a directory: {pathvalue1}")
        return
    if not os.path.isdir(pathvalue3):
        print(f"Error: LOG_DIRECTORY is not a directory: {pathvalue3}")
        return
    if not BucketPathManager.validate_bucket_path(pathvalue2):
        print("Error: BUCKET_PATH format is invalid.")
        return
    # Preflight verification removed
    LOG_FILENAME = current_datetime + "_jetstream_transfer.log"
    LOG_FILENAME_PATH = os.path.join(pathvalue3, LOG_FILENAME)
    logging.basicConfig(filename=LOG_FILENAME_PATH, level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
    if args.print_command:
        include_pattern = r'^.*(?<!\.JPG)$'
        exclude_folders_list = ["_archive", "_YEAR", "ISLAND", "SITE-ID", 'SITE_PHOTOS', 'Corrected', 'corrected', 'uncorrected', "MISC", "DARK", "Products", "Thumbs.db", ".DS_Store", "__pycache__"]
        cmd = generate_gsutil_command(pathvalue1, pathvalue2, [include_pattern], exclude_folders_list, None, args.dry_run, args.threads, args.enable_multi, args.recursive_copy)
        print(cmd)
        return
    do_the_copy(pathvalue1, pathvalue2, pathvalue3, None, None, None, args.dry_run, args.threads, args.enable_multi, args.recursive_copy)
    log_and_print('-------------------------------------------------')
    log_and_print('---- Copy Process Complete ----')

if __name__ == '__main__':
    if '--cli' in sys.argv:
        cli_main()
    else:
        main_gui()