#!__venv__/bin/python3.7
#
# image_focus - simple python utility that helps you decide which which
# of your many photographs has better focus.
#

import argparse
import enum
import os
import sys
import textwrap

import cv2

import src
from src import verbose

from src.remote import GooglePhotosLibrary
from src.display import DisplayHandler
from src.display import MAXIMUM_DISPLAY_SIZE
from src.display import BORDER

from src.image_handler import ImageHandler, RemoteImageHandler


class KEYBOARD(enum.IntEnum):
    """Enum containing all used keyboard keys."""

    ESC = 27
    COMMA = 44
    DOT = 46
    ONE = 49
    LEFT = 81
    RIGHT = 83
    A = 97
    D = 100
    F = 102
    L = 108
    P = 112
    R = 114
    S = 115
    X = 120
    Y = 121
    Z = 122


def get_parser():
    """Get argument parser object."""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
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
        """))

    parser.add_argument("-v", "--verbose", action='store_true',
                        help="show more verbose console output")
    parser.add_argument("images",
                        help="path to the directory with images")
    parser.add_argument("-t", "--treshold", default=0,
                        help="focus treshold for auto choosing (default 0)")
    parser.add_argument("-r", "--remote", action='store_true',
                        help="get images from the Google Photos library")
    parser.add_argument("-l", "--backup-maxlen", default=None, type=int,
                        help="limit size of the backup buffer")
    parser.add_argument("-w", "--without-threading", action='store_false',
                        help="disable background preloading",
                        dest='with_threading')

    return parser


def main():

    # get argument parser and parse given arguments
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose:
        src._verbose = True

    # Initialize GooglePhotosLibrary object for remote connection
    if args.remote:
        try:
            library = GooglePhotosLibrary()
        except FileNotFoundError as err:
            sys.stderr.write(f"{err}\n\n"
                "To run in the remote mode, you must have client_secret.json file with\n"
                "Google API credentials for your application. Note that this file will\n"
                "not be required after the authentication is complete.\n")
            sys.exit(11)

    try:
        if args.remote:
            if not args.with_threading:
                sys.stderr.write(f"Remote mode cannot run without threading\n")
                sys.exit(10)
            handler = RemoteImageHandler(args.images, library, args.backup_maxlen)
        else:
            handler = ImageHandler(args.images, args.with_threading, args.backup_maxlen)
    except IOError as err:
        sys.stderr.write(f"Cannot open directory '{args.images}'\n{err}\n")
        sys.exit(1)

    if len(handler) < 2:
        sys.stderr.write("There are no images to display.\n")
        sys.exit(2)

    try:
        os.mkdir(os.path.join(args.images, 'deleted'))
    except FileExistsError:
        pass
    except OSError as err:
        sys.stderr.write(f"Cannot create 'deleted' folder.\n{err}\n")
        sys.exit(3)

    display = DisplayHandler()

    resize_mode = False
    swap_mode = False
    swap_first = 0

    amount = 2
    rerender = True

    while True:

        if rerender:
            image_objects = handler.get_list(amount)
            display.render(image_objects)

        rerender = False

        key = -1
        while key == -1:
            key = cv2.waitKey(1000)

        if key in [KEYBOARD.LEFT, KEYBOARD.COMMA]:
            rerender = handler.roll_right()

        elif key in [KEYBOARD.RIGHT, KEYBOARD.DOT]:
            rerender = handler.roll_left()

        elif key in [KEYBOARD.A, KEYBOARD.D, KEYBOARD.S]:

            if amount == 1:
                if key != KEYBOARD.D:
                    continue
                idx = 0

            elif amount == 2 and len(handler) > 1:

                if key == KEYBOARD.A:
                    idx = 0
                elif key == KEYBOARD.D:
                    idx = 1

                elif key == KEYBOARD.S:
                    difference = handler.get_relative(0).focus - handler.get_relative(1).focus

                    if abs(difference) < args.treshold:
                        continue

                    idx = int(difference > 0)

            else:
                # These convenient key bindings do nothing for more concatenated photos
                continue

            handler.delete_image(idx, amount)
            rerender = True

        elif key in [KEYBOARD.Y, KEYBOARD.Z]:
            handler.restore_last()
            rerender = True

        elif key == KEYBOARD.F:
            display.toggle_fullscreen()

        elif key == KEYBOARD.P:
            display.toggle_text_embeding()
            rerender = True

        elif key == KEYBOARD.L:
            if swap_mode:
                display.render_border()
            else:
                display.render_border(BORDER.GREEN)
            swap_first = 0
            swap_mode = not swap_mode

        elif key == KEYBOARD.R:
            if resize_mode:
                display.render_border()
            else:
                display.render_border(BORDER.BLUE)
            resize_mode = not resize_mode

        elif key in [KEYBOARD.ESC, KEYBOARD.X]:
            break

        elif KEYBOARD.ONE <= key < KEYBOARD.ONE + MAXIMUM_DISPLAY_SIZE:

            value = key - ord('0')
            if resize_mode:
                resize_mode = False
                amount = value
            elif swap_mode:
                if value > amount:
                    continue
                if swap_first:
                    swap_mode = False
                    handler.swap_images(swap_first - 1, value - 1)
                else:
                    swap_first = value
                    continue
            else:
                if value > amount:
                    continue
                handler.delete_image(value - 1, amount)
            rerender = True

        else:
            verbose(f"Key {key} pressed.")

        if len(handler) < 2:
            break

    del display
    del handler


if __name__ == "__main__":
    main()
