import os
import subprocess
from pathlib import Path
# to get current date & time
from datetime import datetime
from gooey import Gooey, GooeyParser

def do_the_copy(path1,path2,path3):
    subprocess.call(["robocopy", path1 ,path2, "/mt","/XX", "/z", "/mir","/log:" + path3])

@Gooey(program_name='File Copy Tool',
       menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'File Copy',
                'description': 'Python based file copy using robocopy ',
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

    do_the_copy(pathvalue1,pathvalue2,LOG_FILENAME_PATH)
    print('-------------------------------------------------')
    print('---- Copy Process Complete ----')

if __name__ == '__main__':
    main()