#!__venv__/bin/python3.7
#
# image_focus - simple python utility that helps you decide which which
# of your many photographs has better focus.
#
# Few lines of code were inspired by this article:
# https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/
#

import argparse
import enum
import os
import queue
import sys
import textwrap
import threading

from collections import deque

import cv2
import numpy

# global funcion for non verbose printing
verbose = lambda *a, **k: None

# Maximum amount of images displayed at the same time
MAXIMUM_DISPLAY_SIZE = 6


class JOB(enum.Enum):
    """Enum containing job types for background thread worker."""

    LOAD_IMAGE = 1
    CALC_FOCUS = 2
    EXIT = 3


class BORDER(enum.Enum):
    BLUE = [100, 0, 0]


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
    P = 112
    R = 114
    S = 115
    X = 120
    Y = 121
    Z = 122


class Image:

    def __init__(self, filename, path):

        self._filename = filename
        self._path = path

        self._deleted = False
        self._focus = None
        self._base_image = None
        self._image_map = {}

    def load_image(self, focus_only=False):

        def _load_image(path, filename):
            """Get image object or None from given path and filename."""
            return cv2.imread(os.path.join(path, filename))

        def _get_image_focus(image):
            """Get focus value of given image."""
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return cv2.Laplacian(gray, cv2.CV_64F).var()

        # Do nothing if image is deleted
        if self._deleted:
            return

        # Nothing to load if base image already exists
        if self._base_image is not None:
            return

        # Nothing to do if focus was already calculated
        if focus_only and self._focus is not None:
            return

        image = _load_image(self._path, self._filename)
        self._focus = _get_image_focus(image)

        if not focus_only:
            self._base_image = image

    def deload_image(self):
        self._base_image = None
        self._image_map = {}

    def get(self, height=None):

        # Load image if it is not loaded
        if self._base_image is None:
            self.load_image()

        # Return original image if no height was specified
        if height is None:
            return self._base_image

        # Return cached image from the image map
        if height in self._image_map:
            return self._image_map[height]

        current_height, current_width, _ = self._base_image.shape
        new_width = int((height / current_height) * current_width)
        resized = cv2.resize(self._base_image, (new_width, height))

        self._image_map[height] = resized
        return resized

    def delete(self):
        if self._deleted:
            return

        self._deleted = True
        self.deload_image()

        old_file = os.path.join(self._path, self._filename)
        self._path = os.path.join(self._path, "deleted")
        new_file = os.path.join(self._path, self._filename)
        os.rename(old_file, new_file)

    def restore(self):
        if not self._deleted:
            return

        self._deleted = False

        old_file = os.path.join(self._path, self._filename)
        self._path, _ = os.path.split(self._path)
        new_file = os.path.join(self._path, self._filename)
        os.rename(old_file, new_file)

    @property
    def deleted(self):
        return self._deleted

    @property
    def focus(self):
        return self._focus

    @property
    def filename(self):
        return self._filename


class Worker(threading.Thread):
    """Background worker class."""

    # Automatically load image focus when first loading the actual image
    AUTOMATIC_FOCUS = True

    def __init__(self, job_queue):
        """Initialize background image preloading thread.

        arguments:
            job_queue -- priority queue with worker jobs
        """
        threading.Thread.__init__(self)

        self._queue = job_queue

    def run(self):

        while True:
            _, item = self._queue.get()
            job, obj = item

            # stop thread and return back to main one
            if job is JOB.EXIT:
                break

            verbose(f"Background job: {job.name} : {obj.filename}")

            # preload image itself
            if job is JOB.LOAD_IMAGE:
                obj.load_image()

            # calculate focus of an image
            elif job is JOB.CALC_FOCUS:
                obj.load_image(focus_only=True)


class ImageHandler:
    """Class for image carousel handling.

    Background worker is also handled from here.
    """

    PRELOAD_RANGE = 8

    # All allowed image extensions
    ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.png', '.jpeg')

    def __init__(self, path, with_threading=True, backup_maxlen=None):
        """Initialize image handler class.

        arguments:
            path           -- path to the folder with images
            with_threading -- whether to use additional image loading thread
            backup_maxlen  -- maximum size of the backup deque

        Class loads and further handles all images from given directory (it is
        non recursive meaning that subdirectories are not checked) By default
        images in handler are sorted lexicographically and only contains files
        with allowed extensions.
        """

        self._idx = 0
        self._worker = None
        self._job_queue = None
        self._backup = deque(maxlen=backup_maxlen)
        self._path = path

        files = os.listdir(path)  # Throws IOError
        self._filenames = [file for file in files if file.endswith(self.ALLOWED_IMAGE_EXTENSIONS)]
        # NOTE: This way of sorting might not be the most efficient, but it works well
        self._filenames.sort(key=lambda item: item.replace('.', chr(0x01)))

        self._images = {filename: Image(filename, path) for filename in self._filenames}

        if with_threading:
            self._start_worker()

    def __del__(self):
        if self._worker:
            self._end_worker()

    def __len__(self):
        return len(self._filenames)

    def __getitem__(self, key):

        if isinstance(key, int):
            key = self._filenames[key]
        elif not isinstance(key, str):
            raise TypeError("Key must be of instance 'int' or 'str'")

        return self._images[key]

    def get_relative(self, idx):
        return self.__getitem__(self._idx + idx)

    def _load(self, idx):
        if self._worker is None:
            return

        if 0 <= idx <= len(self._filenames) - 2:
            verbose(f'Main: load image {idx}')
            self._job_queue.put((5, (JOB.LOAD_IMAGE, self.__getitem__(idx))))

    def _deload(self, idx):
        if 0 <= idx <= len(self._filenames) - 2:
            verbose(f'Main: deload image {idx}')
            self.__getitem__(idx).deload()

    def roll_right(self):
        """Move the image carousel one image to the right"""
        if self._idx <= 0:
            return False

        self._idx -= 1
        self._load(self._idx - self.PRELOAD_RANGE)
        self._deload(self._idx + self.PRELOAD_RANGE * 2 + 1)
        return True

    def roll_left(self):
        """Move the image carousel one image to the left"""
        if self._idx >= len(self._filenames) - 1:
            return False

        self._idx += 1
        self._load(self._idx + self.PRELOAD_RANGE + 1)
        self._deload(self._idx - self.PRELOAD_RANGE * 2)
        return True

    def delete_image(self, offset, total):
        idx = self._idx + offset
        try:
            obj = self.__getitem__(idx)
        except IndexError:
            return None

        self._backup.append((idx, obj))

        del self._filenames[idx]
        obj.delete()

        if self._idx > 0 and total/2 > offset:
            self._idx -= 1
            self._load(self._idx - self.PRELOAD_RANGE)
        else:
            self._load(self._idx + self.PRELOAD_RANGE + 1)

        return obj

    def restore_last(self):
        """Restore last deleted image."""
        try:
            idx, obj = self._backup.pop()
        except IndexError:
            return None

        filename = obj.filename
        self._filenames.insert(idx, filename)
        self._images[filename].restore()
        return filename

    def get_list(self, limit):
        objects = []
        try:
            for i in range(limit):
                objects.append(self.__getitem__(self._idx + i))
        except IndexError:
            pass

        return objects

    def _start_worker(self):
        """Start background worker."""
        size = len(self._images)
        self._job_queue = queue.PriorityQueue()

        # fill queue with focus jobs and non loaded images
        for i, filename in enumerate(self._filenames):
            self._job_queue.put((size + i, (JOB.CALC_FOCUS, self.__getitem__(filename))))

        for i in range(2, min(self.PRELOAD_RANGE + 1, len(self._filenames))):
            self._job_queue.put((i, (JOB.LOAD_IMAGE, self.__getitem__(i))))

        self._worker = Worker(self._job_queue)
        self._worker.start()

    def _end_worker(self):
        """Stop background worker."""
        self._job_queue.put((0, (JOB.EXIT, None)))
        self._worker.join()


class DisplayHandler:

    # Name of the application window
    WINDOW_NAME = "XDisplay Handler"

    def __init__(self):

        self._enable_text_embeding = True
        self._current = None

        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.WINDOW_NAME, 1280, 640)

    def __del__(self):
        cv2.destroyWindow(self.WINDOW_NAME)

    def _embed_text(self, image, focus, filename):
        if not self._enable_text_embeding:
            return

        cv2.putText(image, f"Focus: {focus:.2f}", (50, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), thickness=20)
        cv2.putText(image, filename, (50, 280),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), thickness=12)

    def toggle_text_embeding(self):
        self._enable_text_embeding = not self._enable_text_embeding

    def toggle_fullscreen(self):
        if not cv2.getWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN):
            cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

    def render_border(self, border=None):
        if not isinstance(border, BORDER) and border is not None:
            raise ValueError("Argument 'border' must be either from BORDER enum or None")

        if border is None:
            image = self._current
        else:
            image = cv2.copyMakeBorder(self._current, 60, 60, 0, 0,
                                       borderType=cv2.BORDER_CONSTANT,
                                       value=border.value)

        cv2.imshow(self.WINDOW_NAME, image)
        cv2.waitKey(1)

    def render(self, image_objects):

        min_height = min(obj.get().shape[0] for obj in image_objects)

        complete = None
        for obj in image_objects:

            image = obj.get(min_height).copy()
            self._embed_text(image, obj.focus, obj.filename)

            if complete is None:
                complete = image
            else:
                complete = numpy.hstack((complete, image))

        self._current = complete

        cv2.imshow(self.WINDOW_NAME, complete)
        cv2.waitKey(1)  # needed to display the image


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
    parser.add_argument("-m", "--multi-window", action='store_true',
                        help="display in multiple windows")
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
        global verbose
        verbose = print

    try:
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
            else:
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
