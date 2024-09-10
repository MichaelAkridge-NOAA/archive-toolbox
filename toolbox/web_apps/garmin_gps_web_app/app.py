import re
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

def gpxconvert(value1, value2):
    fmt = "%Y/%m/%d %H:%M:%S"
    header = 'ident,lat,long,time,ltime'
    GPXfile = value1
    utcoff = value2
    data = GPXfile.read().decode('utf-8')
    
    new_file_name_txt = GPXfile.name.replace('.gpx', '.txt')
    waypoint_name = re.findall(r'<name>([^\<]+)', data)
    lat = re.findall(r'lat="([^\"<]+)', data)
    lon = re.findall(r'lon="([^\"<]+)', data)
    time = re.findall(r'</ele><time>([^\<]+)', data)
    datime = re.findall(r'</ele><time>([^\<]+)', data)
    newltime = []
    
    for i in datime:
        datetime_object = datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ')
        newtime = datetime_object + timedelta(hours=utcoff)
        newltime.append(newtime.strftime(fmt))  # Convert datetime to string
        
    waypoint_data = np.array(list(zip(waypoint_name, lat, lon, time, newltime)))
    
    # Convert numpy array to CSV format
    output = f"{header}\n"
    for row in waypoint_data:
        output += ','.join(row) + '\n'
    
    return output, new_file_name_txt

# Streamlit UI
st.title('GPX to TXT Converter 3.0')

st.write("This app converts Garmin GPX files to a txt/csv format.")

# File uploader for GPX file
gpx_file = st.file_uploader("Choose a GPX file", type="gpx")

# Input for UTC to local offset
utc_offset = st.number_input("Enter UTC to local offset", min_value=-12, max_value=12, value=0)

if gpx_file is not None and st.button('Convert'):
    # Perform conversion and get the output text
    output_text, file_name = gpxconvert(gpx_file, utc_offset)
    
    # Display the converted text file in a text area
    st.text_area("Converted TXT File", output_text, height=300)
    
    # Provide download link for the converted file
    st.download_button(label="Download Converted TXT", data=output_text, file_name=file_name)
