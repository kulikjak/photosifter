import json
import os
import sys

from photosifter.remote import GooglePhotosLibrary


def resolve(args):

    try:
        library = GooglePhotosLibrary()
    except FileNotFoundError as err:
        sys.stderr.write(f"{err}\n\n"
            "To run in the remote mode, you must have client_secret.json file with\n"
            "Google API credentials for your application. Note that this file will\n"
            "not be required after the authentication is complete.\n")
        sys.exit(11)

    try:
        files = os.listdir(args.path)
    except IOError as err:
        sys.stderr.write(f"{err}\n")
        sys.exit(1)

    total = len(files)

    resolved = {}
    for _ in range(args.limit):
        item = library.get_next()
        filename = item['filename']

        if filename in files:
            resolved[filename] = item['productUrl']
            files.remove(filename)
            if args.verbose:
                print(f"[{len(resolved)}/{total}] found {filename}")

        if not files:
            break

    print("Resolved files:")
    if args.dict:
        print(resolved)
    else:
        print(json.dumps(list(resolved.values())))

    if files:
        print("Unresolved files:")
        print(files)
