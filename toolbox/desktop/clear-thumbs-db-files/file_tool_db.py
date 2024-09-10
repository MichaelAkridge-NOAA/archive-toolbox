import os
from gooey import Gooey, GooeyParser

def delete_thumbs_db(pathvalue):
    deleted_files = []
    errors = []

    for root, dirs, files in os.walk(pathvalue):
        for file in files:
            if file.lower() == 'thumbs.db':
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                except FileNotFoundError:
                    errors.append(f"File not found: {file_path}")
                except Exception as e:
                    errors.append(f"Error deleting {file_path}: {e}")

    return deleted_files, errors

@Gooey(
    program_name='Thumbs.db Clear Tool',
    default_size=(700, 700),
    menu=[
        {
            'name': 'Deletes/Clears thumbs.db files ',
            'items': [
                {
                    'type': 'AboutDialog',
                    'menuTitle': 'About',
                    'name': 'Tool',
                    'description': 'Python',
                    'version': '1.0',
                    'copyright': '2022',
                    'website': '',
                    'developer': 'MWA'
                }
            ]
        }
    ]
)
def parse_args():
    parser = GooeyParser(description='App.')
    parser.add_argument('SELECT_FOLDER', widget='DirChooser')
    return parser.parse_args()
def main():
    args = parse_args()
    pathvalue = args.SELECT_FOLDER
    deleted_files, errors = delete_thumbs_db(pathvalue)

    if deleted_files:
        print("Deleted files:")
        for file in deleted_files:
            print(file)

    if errors:
        print("Errors:")
        for error in errors:
            print(error)

if __name__ == '__main__':
    main()
