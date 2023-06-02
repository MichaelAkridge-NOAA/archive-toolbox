import os
import subprocess
from pathlib import Path
# to get current date & time
from datetime import datetime
from gooey import Gooey, GooeyParser
import google
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import logging
import time
#import matplotlib.pyplot as plt
import re
# Define the scopes that your application needs to access Google Cloud Storage
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

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
    
def generate_gsutil_command(path1, path2, include_pattern, exclude_folders_pattern, dry_run, threads, enable_multi, recursive_):
    """
    Generate the gsutil command string based on the provided parameters.
    """
    combined_pattern = f'({include_pattern})|({exclude_folders_pattern})'
    dry_run_flag = "-n" if dry_run else ""
    threads_flag = "-o " + "GSUtil:parallel_thread_count=" + str(threads) if threads else ""
    enable_multi_flag = "-m" if enable_multi else ""
    recursive_flag = "-r" if recursive_ else ""
    gsutil_command = f'gsutil {threads_flag} {enable_multi_flag} rsync {recursive_flag} {dry_run_flag} -x "{combined_pattern}" "{path1}" "{path2}"'
    return gsutil_command

def do_the_copy(path1, path2, path3, dry_run, threads, enable_multi, recursive_):
    """
    Run the gsutil command for copying files based on the provided parameters.
    """    
    include_pattern = r'^.*(?<!\.JPG)$'
    exclude_folders_list = ["_archive", "_YEAR", "ISLAND", "SITE-ID",'SITE_PHOTOS', 'Corrected','corrected','uncorrected',"MISC", "DARK", "Products"]
    exclude_folders_pattern = '|'.join([f'.*{folder}.*' for folder in exclude_folders_list])
    gsutil_command = generate_gsutil_command(path1, path2, include_pattern, exclude_folders_pattern, dry_run, threads, enable_multi, recursive_)
    print("Running Sync Script:")
    print("    ")
    print(gsutil_command)
    # Run gsutil command and capture output
    start_time = time.time()
    process = subprocess.Popen(gsutil_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()
    elapsed_time = time.time() - start_time
    if process.returncode == 0:
        log_and_print('Output:')
        log_and_print(output.decode())
    else:
        log_and_print('---- Copy Process Failed ----')
        log_and_print('Error:')
        log_and_print(output.decode())
        
@Gooey(program_name='NOAA Open Data Dissemination (NODD)',
       default_size=(700, 700),   # starting size of the GUI
       image_dir='./_icons',
       menu=[{
        'name': 'NODD File Upload Tool',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'File Copy',
                'description': 'Python based file upload using gsutil',
                'version': '1.0',
                'copyright': '2022',
                'website': '',
                'developer': 'Michael Akridge'}]}])

def parse_args():
    """Parses command-line arguments for the script."""
    parser = GooeyParser(description='Upload Tool')
    parser.add_argument('COPY_FROM', widget='DirChooser')
    parser.add_argument('COPY_TO_PATH', widget='TextField')
    parser.add_argument('COPY_LOG_PATH', widget='DirChooser')
    # Add an option to turn on/off the -n flag
    parser.add_argument('--dry-run', action='store_true', help='This flag performs a "dry run," which means that the synchronization will be simulated, and no actual data will be transferred. ')
    # Add an option to turn on/off the -o flag
    parser.add_argument('--threads', type=int, default=12, widget='Slider', help='Number of threads to use for the transfer. Helps with bandwidth throttling.',
                        gooey_options={
                            'min': 1,
                            'max': 24
                        })
    parser.add_argument('--enable-multi', action='store_true', help='This flag enables multi-threading, which speeds up the transfer by using multiple connections.')
    parser.add_argument('--recursive-copy', action='store_true', help='This flag tells rsync to perform a recursive copy of the entire directory tree.')
    parser.add_argument('--print-command', action='store_true', help='Print the gsutil command instead of running it')
    return parser.parse_args()

def main():
    args = parse_args()
    current_datetime = datetime.now().strftime("%m_%d_%Y_%H%M")
    pathvalue1 = args.COPY_FROM
    pathvalue2 = "gs://" + args.COPY_TO_PATH
    pathvalue3 = args.COPY_LOG_PATH
    LOG_FILENAME = current_datetime + "_nodd_transfer.log"
    LOG_FILENAME_PATH = os.path.join(pathvalue3, LOG_FILENAME)
    logging.basicConfig(filename=LOG_FILENAME_PATH, level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')

    if args.print_command:
        print("gsutil command:")
        print("    ")
        include_pattern = r'^.*(?<!\.JPG)$'
        exclude_folders_list = ["_archive", "_YEAR", "ISLAND", "SITE-ID",'SITE_PHOTOS', 'Corrected','corrected','uncorrected',"MISC", "DARK", "Products"]
        exclude_folders_pattern = '|'.join([f'.*{folder}.*' for folder in exclude_folders_list])
        gsutil_command = generate_gsutil_command(pathvalue1, pathvalue2, include_pattern, exclude_folders_pattern, args.dry_run, args.threads, args.enable_multi, args.recursive_copy)
        print(gsutil_command)
    else:
        do_the_copy(pathvalue1, pathvalue2, pathvalue3, args.dry_run, args.threads, args.enable_multi, args.recursive_copy)
        log_and_print('-------------------------------------------------')
        log_and_print('---- Copy Process Complete ----')

if __name__ == '__main__':
    main()