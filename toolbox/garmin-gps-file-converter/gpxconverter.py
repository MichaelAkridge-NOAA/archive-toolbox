import re
#import sys
import numpy as np
#import pandas as pd
#import datetime
from datetime import datetime, timedelta
from gooey import Gooey, GooeyParser


def gpxconvert(value1,value2):
    fmt = "%Y/%m/%d %H:%M:%S"
    header = 'ident,lat,long,time,ltime'
    GPXfile = value1
    utcoff = value2
    data = open(GPXfile).read()
    new_file_name_txt = GPXfile.replace('.gpx', '.txt')
    waypoint_name = re.findall(r'<name>([^\<]+)',data)
    lat = re.findall(r'lat="([^\"<]+)',data)
    lon = re.findall(r'lon="([^\"<]+)',data)
    time = re.findall(r'</ele><time>([^\<]+)',data)
    datime = re.findall(r'</ele><time>([^\<]+)',data)
    newltime = []
    for i in datime:
      datetime_object = datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ')
      newtime = datetime_object + timedelta(hours=utcoff)
      newltime.append(newtime)
    waypoint_data = np.array(list(zip(waypoint_name,lat,lon,time,newltime)))
    np.savetxt(new_file_name_txt, waypoint_data, delimiter=",", fmt='%s',comments='', header = header)

@Gooey(
    program_name='GPX to TXT Converter 2.1',
    menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'GPX to TXT Converter',
                'description': 'Python based converter for Garmin GPX files',
                'version': '2.1',
                'copyright': '2022',
                'website': '',
                'developer': 'Michael Akridge'}]
        
    }]
)

def parse_args():
    parser = GooeyParser(description='GPX to TXT Converter. Converts Garmin GPX files to a txt/csv format.')
    parser.add_argument('UTC_TO_LOCAL_OFFSET',type=float)
    parser.add_argument('FILE_PATH', widget="FileChooser")
    return parser.parse_args()

def main():
    args = parse_args()
    
    utcoffset = args.UTC_TO_LOCAL_OFFSET
    filevalue = args.FILE_PATH
    gpxconvert(filevalue,utcoffset)
    
if __name__ == '__main__':
    main()

