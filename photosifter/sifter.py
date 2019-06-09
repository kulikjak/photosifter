import enum
import os
import sys
import cv2

from photosifter.util import verbose

from photosifter.remote import GooglePhotosLibrary
from photosifter.display import DisplayHandler
from photosifter.display import MAXIMUM_DISPLAY_SIZE
from photosifter.display import BORDER

from photosifter.image_handler import ImageHandler
from photosifter.image_handler import RemoteImageHandler

# Don't really care about to many variables/branches/statements....
# pylint: disable=R0914,W0212,R0912,R0915


class KEY(enum.IntEnum):
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


def sift(args):

    # Initialize GooglePhotosLibrary object for remote connection
    if args.action == "remote":
        try:
            library = GooglePhotosLibrary()
        except FileNotFoundError as err:
            sys.stderr.write(f"{err}\n\n"
                "To run in the remote mode, you must have client_secret.json file with\n"
                "Google API credentials for your application. Note that this file will\n"
                "not be required after the authentication is complete.\n")
            sys.exit(11)

    try:
        if args.action == "remote":
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

        if key in [KEY.LEFT, KEY.COMMA]:
            rerender = handler.roll_right()

        elif key in [KEY.RIGHT, KEY.DOT]:
            rerender = handler.roll_left()

        elif key in [KEY.A, KEY.D, KEY.S]:

            if amount == 1:
                if key != KEY.D:
                    continue
                idx = 0

            elif amount == 2 and len(handler) > 1:

                if key == KEY.A:
                    idx = 0
                elif key == KEY.D:
                    idx = 1

                elif key == KEY.S:
                    difference = handler.get_relative(0).focus - handler.get_relative(1).focus

                    if abs(difference) < args.threshold:
                        continue

                    idx = int(difference > 0)

            else:
                # These convenient key bindings do nothing for more concatenated photos
                continue

            handler.delete_image(idx, amount)
            rerender = True

        elif key in [KEY.Y, KEY.Z]:
            handler.restore_last()
            rerender = True

        elif key == KEY.F:
            display.toggle_fullscreen()

        elif key == KEY.P:
            display.toggle_text_embeding()
            rerender = True

        elif key == KEY.L:
            if swap_mode:
                display.render_border()
            else:
                display.render_border(BORDER.GREEN)
            swap_first = 0
            swap_mode = not swap_mode

        elif key == KEY.R:
            if resize_mode:
                display.render_border()
            else:
                display.render_border(BORDER.BLUE)
            resize_mode = not resize_mode

        elif key in [KEY.ESC, KEY.X]:
            break

        elif KEY.ONE <= key < KEY.ONE + MAXIMUM_DISPLAY_SIZE:

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
