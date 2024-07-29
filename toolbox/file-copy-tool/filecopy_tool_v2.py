import os
import subprocess
from pathlib import Path
from datetime import datetime
from gooey import Gooey, GooeyParser
import platform

def do_the_copy(path1, path2, path3):
    current_os = platform.system()
    if current_os == "Windows":
        subprocess.call(["robocopy", path1, path2, "/mt", "/XX", "/z", "/mir", "/log:" + path3])
    elif current_os == "Darwin" or current_os == "Linux":
        log_file = open(path3, "w")
        subprocess.call(["rsync", "-avz", path1 + "/", path2], stdout=log_file)
        log_file.close()
    else:
        print("Unsupported operating system: " + current_os)

@Gooey(program_name='File Copy Tool',
       menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'File Copy',
                'description': 'Python-based file copy using robocopy or rsync',
                'version': '1.0',
                'copyright': '2022',
                'website': '',
                'developer': 'Michael Akridge'}]}])

def parse_args():
    parser = GooeyParser(description='Folder Size Stat App.')
    parser.add_argument('COPY_FROM', widget='DirChooser')
    parser.add_argument('COPY_TO_PATH', widget='DirChooser')
    parser.add_argument('COPY_LOG_PATH', widget='DirChooser')
    return parser.parse_args()

def main():
    args = parse_args()
    current_datetime = datetime.now().strftime("%m_%d_%Y_%H%M")
    pathvalue1 = args.COPY_FROM
    pathvalue2 = args.COPY_TO_PATH
    pathvalue3 = args.COPY_LOG_PATH
    LOG_FILENAME = current_datetime + "_filecopy_log.log"
    LOG_FILENAME_PATH = os.path.join(pathvalue3, LOG_FILENAME)

    do_the_copy(pathvalue1, pathvalue2, LOG_FILENAME_PATH)
    print('-------------------------------------------------')
    print('---- Copy Process Complete ----')

if __name__ == '__main__':
    main()

