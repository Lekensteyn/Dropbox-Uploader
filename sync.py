#!/usr/bin/env python3
# Uploads new files only (skip existing files)

from argparse import ArgumentParser
import os, subprocess, sys

# Path to dropbox_uploader.sh (assume relative to this script)
DU_PROGRAM = os.path.join(os.path.dirname(__file__), "dropbox_uploader.sh")

# Parse command-line arguments.
parser = ArgumentParser(description="Sync new files to Dropbox")
parser.add_argument("local_dir", help='Local source directory')
parser.add_argument("remote_dir", help='Local source directory')
args = parser.parse_args()
srcdir = args.local_dir
# Ensure that destination ends with a slash (directory instead of file)
destdir = args.remote_dir.rstrip('/') + '/'
# You could also comment out the above lines and hard-code parameters:
# srcdir = "..."
# destdir = ".../"

def get_remote_files(dirname):
    list_cmd = [DU_PROGRAM, "list", dirname]
    # Execute command and parse output
    with subprocess.Popen(list_cmd, stdout=subprocess.PIPE) as proc:
        # Possible output (for non-existing file or a file)
        # > Listing "/dir/"... FAILED
        # > Listing "/dir/"... FAILED: /dir is not a directory!
        items = []
        for line in proc.stdout:
            # Parse output bytes as ASCII string (could also use utf-8)
            line = line.decode('ascii').strip()
            # Skip empty lines
            if not line:
                continue

            # Has the user ran dropbox_uploader.sh before to set API keys?
            if "This is the first time" in line:
                raise RuntimeError("Please configure a key first!")

            # Was it possible to open the dir?
            if "FAILED" in line:
                break

            file_type, size, filename = line.split(maxsplit=2)
            if file_type == ">":
                # ignore " > Listing "/dir/"... DONE"
                continue
            if file_type == "[D]":
                print("Directory recursion not supported. Found", filename)
                # Could recurse here if wanted...
                pass
            if file_type != "[F]":
                print("Not a file:", filename, file=sys.stderr)
                continue
            # Found " [F] 7102 README.md"
            items.append(filename)
    return items

# Find local files...
src_items = os.listdir(srcdir)
# Find files that exist on the remote...
remote_files = get_remote_files(destdir)
# ...and drop already synced files
new_local_files = set(src_items).difference(remote_files)

if not new_local_files:
    print("Everything is synced!")
    sys.exit(0)

# The command to upload remaining files
sync_cmd = [DU_PROGRAM, "upload"]
for filename in new_local_files:
    sync_cmd.append(os.path.join(srcdir, filename))
sync_cmd.append(destdir)

# Note: the command is not escaped so you cannot
# copy & paste output if it contains spaces.
print("Executing:", ' '.join(sync_cmd))

# Exit python, hand over control to the upload command
os.execv(DU_PROGRAM, sync_cmd)
