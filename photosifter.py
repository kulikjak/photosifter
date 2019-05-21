#!__venv__/bin/python3.7

import argparse
import textwrap

import src

from src.resolver import resolve
from src.sifter import sift


def display_guide():
    # TODO - write this guide better....
    guide = """
        keyboard shortcuts:
           <Left> ,             move left
           <Right> .            move right
           <Esc> X              close the application
           J K L                switch between view modes
           Y Z                  revert last deletion
           A D                  delete left/right image (only in DISPLAY_BOTH mode)
           S                    delete image with worse focus value
                                   (deletes current in DISPLAY_lEFT or DISPLAY_RIGHT modes)
           F                    toggle fullscreen
    """
    print(textwrap.dedent(guide))


def get_parser():
    """Get argument parser object."""

    # Create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="show more verbose console output")

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
    local_parser.add_argument("-t", "--treshold", default=0,
        help="focus treshold for auto choosing (default 0)")
    local_parser.add_argument("-l", "--backup-maxlen", default=None, type=int,
        help="limit size of the backup buffer")
    local_parser.add_argument("-w", "--without-threading", action='store_false',
        help="disable background preloading",
        dest='with_threading')

    # remote sifting related arguments
    remote_parser.add_argument("images",
        help="path to the directory with images")
    remote_parser.add_argument("-t", "--treshold", default=0,
        help="focus treshold for auto choosing (default 0)")
    remote_parser.add_argument("-l", "--backup-maxlen", default=None, type=int,
        help="limit size of the backup buffer")

    # relover related arguments
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
        src._verbose = True

    if args.action in ['local', 'remote']:
        sift(args)

    elif args.action == 'guide':
        display_guide()

    elif args.action == 'resolve':
        resolve(args)


if __name__ == "__main__":
    main()
