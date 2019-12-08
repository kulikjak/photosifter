import os
import sys

from photosifter.image import Image
from photosifter.remote import GooglePhotosLibrary


def download(args):

    try:
        library = GooglePhotosLibrary()
    except FileNotFoundError as err:
        sys.stderr.write(f"{err}\n\n"
            "To run in the remote mode, you must have client_secret.json file with\n"
            "Google API credentials for your application. Note that this file will\n"
            "not be required after the authentication is complete.\n")
        sys.exit(11)

    if not os.path.exists(args.images):
        os.makedirs(args.images)

    for i, _ in enumerate(range(args.amount)):
        mediaItem = library.get_next()
        filename = mediaItem['filename']

        print(f"[{i+1}/{args.amount}]: {filename}")

        obj = Image(filename, args.images, mediaItem)
        obj.download_image()

    print("Done")
