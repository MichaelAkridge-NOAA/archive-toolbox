#import re
#import numpy as np
import os
import stat
import pandas as pd
import csv
from datetime import datetime
from gooey import Gooey, GooeyParser

def get_tree_size(path):
    total = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total

def search_folders(path):
    # define empty data list to be used in file metadata script
    final_datas = []
    df = pd.DataFrame()
    for src_dir, dirs, files in os.walk(path):
        for dir_ in dirs:
            current_src = os.path.join(src_dir, dir_)
            print(current_src)
            print('Scanning ' + current_src)
            a= get_tree_size(current_src)
            # returns path size in mb
            b= a/1048576
            # returns path size in gb
            c=a/1073741824
            # returns path size in tb
            d=a/float(1<<40)
            final_data = current_src,d,c,b
            final_datas.append(final_data)
            print("Size: " + str(c) + " GB")
        df = pd.DataFrame(final_datas)
        #use break to just get first loop, root directory, stats
        break
    return df

def check_slash(string):
    slash_to_add = "\\"
    if string and len(string) > 3:
        return string
    else:
        newvalue = os.path.join(string,slash_to_add)
        return newvalue

@Gooey(program_name='Folder Stats',
       menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'Folder Size Stats',
                'description': 'Python based file tree stat maker',
                'version': '1.0',
                'copyright': '2022',
                'website': '',
                'developer': 'Michael Akridge'}]}])

def parse_args():
    parser = GooeyParser(description='Folder Size Stat App.')
    parser.add_argument('SELECT_PATH', widget='DirChooser',type=check_slash)
    return parser.parse_args()

def main():
    # create csv list of files with metadta
    header = ['Path', 'Size(TB)','Size(GB)','Size(MB)']
    # setup  file name & path
    current_datetime = datetime.now().strftime("%m_%d_%Y_%H%M")
    file_log_filename = current_datetime + '_folder_size_log.csv'    
    args = parse_args()
    pathvalue = args.SELECT_PATH
    print(pathvalue)
    df=search_folders(pathvalue)
    file_log_filename_path = os.path.join(pathvalue, file_log_filename) 
    df.to_csv(file_log_filename_path, index=False, header=header)
    print('-------------------------------------------------')
    print('---- Scan Complete ----')
    print('---- Folder Size Log Located at ----')
    print(file_log_filename_path)

if __name__ == '__main__':
    main()
