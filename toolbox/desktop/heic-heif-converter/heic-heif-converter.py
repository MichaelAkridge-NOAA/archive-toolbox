import os
from PIL import Image
from pillow_heif import register_heif_opener
from gooey import Gooey, GooeyParser
# Iterate through all the HEIC files in the directory

def convert_images(path):
    register_heif_opener()
    for root, dirs, files in os.walk(path, topdown=True):
        for i,f in enumerate(files, start=1):
            #COPY_FROM = Path(root)
            input_file = os.path.join(root, f)
            print('file:'+input_file)
            if input_file.endswith(".heic") or input_file.endswith(".heif"):
                try:
                    with Image.open(input_file) as im:
                        im = im.convert("RGB")
                        output_file = os.path.join(root, os.path.splitext(f)[0] + ".JPG")
                        im.save(output_file, "JPEG")
                except:
                    print(f"Error: {f} is not a valid HEIC or HEIF file")
            else:
                print(f"Error: {f} is not a valid image file")

def check_slash(string):
    slash_to_add = "\\"
    if string and len(string) > 3:
        return string
    else:
        newvalue = os.path.join(string,slash_to_add)
        return newvalue
@Gooey(program_name='HEIC and HEIF Converter - HEIC/HEIF to JPG.',
       menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'HEIC and HEIF Converter - HEIC/HEIF to JPG.',
                'description': 'Python based HEIC and HEIF Converter - HEIC/HEIF to JPG.',
                'version': '1.0',
                'copyright': '',
                'website': '',
                'developer': 'Michael Akridge'}]}])

def parse_args():
    parser = GooeyParser(description='HEIC and HEIF Converter')
    parser.add_argument('SELECT_PATH', widget='DirChooser',type=check_slash)
    return parser.parse_args()

def main():
    # setup  file path
    args = parse_args()
    pathvalue = args.SELECT_PATH
    print(pathvalue)
    convert_images(pathvalue)
    print('----  Working ----')
    print('-------------------------------------------------')
    print('----  Complete ----')

if __name__ == '__main__':
    main()