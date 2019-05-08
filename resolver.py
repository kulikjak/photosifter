#!__venv__/bin/python3.7

import argparse
import json
import os
import sys

from src.remote import GooglePhotosLibrary


def main():

    parser = argparse.ArgumentParser(
        description="Search product URLs based on local filenames.")
    parser.add_argument("-l", "--limit", type=int, default=1000,
        help="Limit number of photos remotely searched.")
    parser.add_argument("-d", "--dict", action="store_true",
        help="Print dictionary rather than list of urls.")
    parser.add_argument("-v", "--verbose", action='store_true',
        help="show more verbose console output")
    parser.add_argument("path",
        help="Path to the to-be-resolved folder.")
    args = parser.parse_args()

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


if __name__ == "__main__":
    main()
