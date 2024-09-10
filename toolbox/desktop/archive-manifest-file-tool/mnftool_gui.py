# Import the libraries we need for this script
import hashlib
import optparse
import os
import os.path
import sys
from gooey import Gooey, GooeyParser

def read_hash_from_md5_file(md5_filename):
    """This function reads a hash out of a .md5 file."""

    with open(md5_filename) as file:
        for line in file:
            possible_hash = pos = line.split(",")[1]
            if len(possible_hash) == 32:
                return possible_hash

    return None  # failed to find the hash


def generate_md5_hash(filename, block_size=2 ** 20, progress_blocks=128):
    """This function generates an md5 hash for a given file."""

    md5 = hashlib.md5()
    blocks = 0
    total_blocks = 1 + (os.path.getsize(filename) / block_size)
    with open(filename, 'rb') as file:
        while True:
            data = file.read(block_size)
            if not data:
                break
            md5.update(data)
            # Display progress in the command line
            if (blocks % progress_blocks) == 0:
                percentage_string = "{0}%".format(100 * blocks / total_blocks)
                sys.stdout.write("\r{1:<10}{0}".format(filename, percentage_string))
                sys.stdout.flush()
            blocks += 1
    return md5.hexdigest()


def check_against_md5_file(filename, md5_filename):
    """This function checks a filename against its md5 filename."""

    # Get the expected hash from the .md5 file
    expected_hash = read_hash_from_md5_file(md5_filename)

    # If we couldn't read the expected hash, return an error
    if expected_hash is None:
        print("ERROR     {0}".format(filename))
        print("Could not read a valid md5 hash from {0}".format(md5_filename))
        return (filename, 'could not read from .md5 file', 'not generated')

    # Generate the actual hash for the file being protected
    actual_hash = generate_md5_hash(filename)

    # Print out success or failure messages
    error = None
    if actual_hash == expected_hash:
        sys.stdout.write("\rOK        {0}\n".format(filename))
        sys.stdout.flush()
    else:
        sys.stdout.write("\rERROR     {0}\n".format(filename))
        sys.stdout.flush()
        print("  expected hash  {0}".format(expected_hash))
        print("  actual hash is {0}".format(actual_hash))
        error = (filename, expected_hash, actual_hash)

    return error


def generate_md5_file_for(filename, md5_filename):
    """This function generates an md5 file for an existing file."""
    try:
        output_file = open(md5_filename, 'w')
    except IOError:
        sys.stdout.write("ERROR: can't write to file {0}\n".format(md5_filename))

    generated_hash = generate_md5_hash(filename)
    file_size = os.path.getsize(filename)
    output_file.write("{0},{1},{2}\n".format(os.path.basename(filename),generated_hash,file_size))
    output_file.close()

    sys.stdout.write("\rDONE        {0}\n".format(filename))
    sys.stdout.flush()


def get_file_info_dictionaries(dirs):
    """Walk the directories recursively and match up .mnf files to the files they describe."""

    # Recursively walk the directories, trying to pair up the .md5 files
    file_info_dicts = {}
    for (dirpath, dirnames, filenames) in os.walk(dirs):
        for each_filename in filenames:
            full_file_path = os.path.join(dirpath, each_filename)
            is_md5_file = (full_file_path[-4:].lower() == '.mnf')
            if is_md5_file:
                key = full_file_path[:-4]
            else:
                key = full_file_path
            d = file_info_dicts.setdefault(key, dict(file=False, md5=False))
            if is_md5_file:
                d['md5'] = True
            else:
                d['file'] = True

    # Print information about what was found
    files_found = 0
    md5_found = 0
    both_found = 0
    for file_name, d in iter(file_info_dicts.items()):
        if d['md5'] and d['file']:
            both_found += 1
        elif d['file']:
            files_found += 1
        elif d['md5']:
            md5_found += 1

    print("Found {0} files with matching .mnf files.".format(both_found))
    print("Found {0} .mnf files with no matching file.".format(md5_found))
    print("Found {0} files with no matching .mnf file.".format(files_found))

    return file_info_dicts

@Gooey(
    program_name='Mnftool',
    menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'Mnftool',
                'description': 'Python based',
                'version': '2.1',
                'copyright': '2022',
                'website': '',
                'developer': 'Michael Akridge'}]
        
    }]
)


def parse_args():
    parser = GooeyParser(description='MNF Tool Checker & Generator.')    
    parser.add_argument('SELECT_FILE_FOLDER', widget="DirChooser")
    parser.add_argument('SELECT_OPERATION',choices=['check','generate'])
    return parser.parse_args()

def main():
    args = parse_args()
    dirs = args.SELECT_FILE_FOLDER
    operation = args.SELECT_OPERATION
    file_info_dicts = get_file_info_dictionaries(dirs)
    if operation == 'check':
        # Check each pair of matching files
        num_checked = 0
        errors = []
        for filename, d in sorted(iter(file_info_dicts.items())):
            if d['file'] and d['md5']:
                error = check_against_md5_file(filename, filename + '.mnf')
                if error:
                    errors.append(error)
                num_checked += 1
        print("===============================================================")
        print("SUMMARY")
        print("{0} files checked.".format(num_checked))
        print("{0} had errors.".format(len(errors)))
        for (filename, expected_hash, actual_hash) in errors:
            print(filename)
            print("  expected hash  {0}".format(expected_hash))
            print("  actual hash is {0}".format(actual_hash))
        print("===============================================================")

    elif operation == 'generate':
        print(file_info_dicts)
	# Generate an .md5 file for files which don't have one
        for filename, d in sorted(iter(file_info_dicts.items())):
            if d['file'] and not d['md5']:
                generate_md5_file_for(filename, filename + '.mnf')
        print("===============================================================")


if __name__ == "__main__":
    main()
