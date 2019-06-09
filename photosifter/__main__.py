#!/usr/bin/env python3

import argparse
import textwrap

from photosifter import util
from photosifter import remote

from photosifter.display import MAXIMUM_DISPLAY_SIZE
from photosifter.resolver import resolve
from photosifter.sifter import sift


def display_guide():
    guide = """        Photosifter is a simple application to sift through photos or images ...

        Modes:

          Local:
            Sift through images in a given folder.

          Remote:
            Same as local mode but works with remote Google images. Tha application needs google
            API secret and credentials to work remotely.

          Resolve:
            Find remote URLs of images based on their filenames. Note that this might not work
            correctly if multiple images have the same filename. The number of searched images
            is limited by default. Keyboard shortcuts bellow does not apply to this one.

          Guide:
            Not really a mode, just this guide.

        Keyboard shortcuts:

          Global:
            <Left> | ,           move left
            <Right> | .          move right
            <Esc> | X            close the application
            <Number>             delete image on nth shown position (nothing for not shown).
            Y | Z                revert last deletion
            P                    toggle text info (focus and filename)
            F                    toggle fullscreen
            R                    toggle resize mode
            L                    toggle swap mode

          Resize mode:  [blue border]
            Change number of concurrently displayed images by pressing desired number (1-{})

          Swap mode:    [green border]
            Swap two images in the carousel by pressing position of both of them.

          Size-dependent shortcuts:
            These additional shortcuts are different based on the number of displayed images.

            D                    delete current image                   [single image only]
            A / D                delete left/right image                [double image only]
            S                    delete image with worse focus value    [double image only]
    """.format(MAXIMUM_DISPLAY_SIZE)
    print(textwrap.dedent(guide))


def get_parser():
    """Get argument parser object."""

    # Create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="show more verbose console output")
    parser.add_argument("-f", "--forget-user", action='store_true',
                        help="forget previously remembered user")

    # create all subparsers
    subparsers = parser.add_subparsers(dest='action')
    subparsers.add_parser('guide', add_help=False,
        help='Display guide to this program and its controls.')

    local_parser = subparsers.add_parser('local',
        help='Sift through local images.')
    remote_parser = subparsers.add_parser('remote',
        help='Sift through images from remote Google Photos library.')
    resolve_parser = subparsers.add_parser('resolve',
        help='Search remote product URLs based on local filenames.')

    # local sifting related arguments
    local_parser.add_argument("images",
        help="path to the directory with images")
    local_parser.add_argument("-t", "--threshold", default=0,
        help="focus threshold for auto choosing (default 0)")
    local_parser.add_argument("-l", "--backup-maxlen", default=None, type=int,
        help="limit size of the backup buffer")
    local_parser.add_argument("-w", "--without-threading", action='store_false',
        help="disable background preloading",
        dest='with_threading')

    # remote sifting related arguments
    remote_parser.add_argument("images",
        help="path to the directory with images")
    remote_parser.add_argument("-t", "--threshold", default=0,
        help="focus threshold for auto choosing (default 0)")
    remote_parser.add_argument("-l", "--backup-maxlen", default=None, type=int,
        help="limit size of the backup buffer")

    # resolver related arguments
    resolve_parser.add_argument("-l", "--limit", type=int, default=1000,
        help="Limit number of photos remotely searched.")
    resolve_parser.add_argument("-d", "--dict", action="store_true",
        help="Print dictionary rather than list of urls.")
    resolve_parser.add_argument("path",
        help="Path to the to-be-resolved folder.")

    return parser


def main():

    # get argument parser and parse given arguments
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose:
        util.enable_verbose = True

    if args.action in ['local', 'remote']:
        sift(args)

    elif args.action == 'guide':
        display_guide()

    elif args.action == 'resolve':
        resolve(args)

    if args.forget_user:
        remote.forget_credentials()


if __name__ == "__main__":
    main()
