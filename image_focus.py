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
import threading

import cv2
import numpy

# global funcion for non verbose printing
verbose = lambda *a, **k: None

# Name of the application window
WINDOW_NAME = 'Image focus'

# All allowed image extensions
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.png', '.jpeg']


class JOB(enum.Enum):
    """Enum containing job types for background thread worker."""

    LOAD_IMAGE = 1
    CALC_FOCUS = 2
    EXIT = 3


class KEYBOARD(enum.IntEnum):
    """Enum containing all used keyboard keys."""

    ESC = 27
    LEFT = 81
    RIGHT = 83
    A = 97
    D = 100
    F = 102
    S = 115
    X = 120


def get_image_focus(image):
    """Get focus value of given image."""

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def load_image(path, filename):
    """Get image object or None from given path and filename."""

    return cv2.imread(os.path.join(path, filename))


class Worker(threading.Thread):
    """Background worker class."""

    # Automatically load image focus when first loading the actual image
    AUTOMATIC_FOCUS = True

    def __init__(self, job_queue, image_map, path):
        """Initialize background thread.

        arguments:
            job_queue -- priority queue with worker jobs
            image_map -- dict with filenames as keys for preloaded values
            path      -- path to folder with images
        """
        threading.Thread.__init__(self)

        self._path = path
        self._queue = job_queue
        self._image_map = image_map

    def run(self):

        while True:
            _, item = self._queue.get()
            job, filename = item

            verbose(f"Background job: {job.name} : {filename}")

            # stop thread and return back to main one
            if job is JOB.EXIT:
                break

            # check if image was not deleted since the job was added into the queue
            if filename not in self._image_map:
                continue

            # preload image itself
            elif job is JOB.LOAD_IMAGE:
                image = load_image(self._path, filename)
                if filename in self._image_map:
                    self._image_map[filename]['image'] = image

                if self.AUTOMATIC_FOCUS:
                    # we can save focus of this image right away as well
                    if self._image_map[filename]['focus'] is None:
                        focus = get_image_focus(image)
                        self._image_map[filename]['focus'] = focus

            # calculate focus of an image
            elif job is JOB.CALC_FOCUS:
                image = load_image(self._path, filename)
                focus = get_image_focus(image)
                if filename in self._image_map:
                    self._image_map[filename]['focus'] = focus


def get_images(path):
    """Get all image filenames from given path.

    Function is non recursive meaning that subdirectories are not checked.
    Returned list is sorted lexicographically and only contains files with
    allowed extensions.
    """

    try:
        files = os.listdir(path)
    except IOError as err:
        sys.stderr.write(f"Cannot open directory '{path}'\n{err}\n")
        sys.exit(1)

    images = [file for file in files if file.endswith(tuple(ALLOWED_IMAGE_EXTENSIONS))]
    images.sort()

    return images


class ImageHandler:
    """Class for image carousel handling.

    Background worker is also handled from here.
    """

    PRELOAD_RANGE = 8

    def __init__(self, path, filenames):
        """Initialize image handler class.

        arguments:
            path      -- path to the folder with images
            filenames -- list of filenames

        Background worker is not initialized here - it is rather created and
        ran from the 'start_worker' member function.
        """

        self._path = path
        self._filenames = filenames
        self._images = {filename: {"filename": filename,
                                   "focus": None,
                                   "image": None} for filename in filenames}

        self._idx = 0
        self._worker = None
        self._job_queue = None

    def __len__(self):
        return len(self._filenames)

    def _load(self, idx):
        if self._worker is None:
            return

        if 0 <= idx <= len(self._filenames) - 2:
            verbose(f'Main: load image {idx}')
            key = self._filenames[idx]
            self._job_queue.put((5, (JOB.LOAD_IMAGE, key)))

    def _deload(self, idx):
        if 0 <= idx <= len(self._filenames) - 2:
            verbose(f'Main: deload image {idx}')
            key = self._filenames[idx]
            self._images[key]['image'] = None

    def _get_image(self, key):
        single = self._images[key]

        # handle lazy background worker
        if single['image'] is None:
            single['image'] = load_image(self._path, key)
        if single['focus'] is None:
            single['focus'] = get_image_focus(single['image'])

        return single

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
        if self._idx >= len(self._filenames) - 2:
            return False

        self._idx += 1
        self._load(self._idx + self.PRELOAD_RANGE + 1)
        self._deload(self._idx - self.PRELOAD_RANGE * 2)
        return True

    def delete_left(self):
        """Delete current left image from the carousel"""
        key = self._filenames[self._idx]
        del self._filenames[self._idx]
        del self._images[key]

        if self._idx > 0:
            self._idx -= 1
            self._load(self._idx - self.PRELOAD_RANGE)
        else:
            self._load(self._idx + self.PRELOAD_RANGE + 1)

    def delete_right(self):
        """Delete current right image from the carousel"""
        key = self._filenames[self._idx + 1]
        del self._filenames[self._idx + 1]
        del self._images[key]

        if self._idx > len(self._images) - 2:
            self._idx -= 1
            self._load(self._idx - self.PRELOAD_RANGE)
        else:
            self._load(self._idx + self.PRELOAD_RANGE + 1)

    @property
    def left(self):
        """Get current left image"""
        key = self._filenames[self._idx]
        return self._get_image(key)

    @property
    def right(self):
        """Get current right image"""
        key = self._filenames[self._idx + 1]
        return self._get_image(key)

    @property
    def current(self):
        """Get both current images in one tuple"""
        return self.left, self.right

    def start_worker(self):
        """Start background worker."""
        if self._worker is not None:
            return False

        size = len(self._images)
        self._job_queue = queue.PriorityQueue()

        # fill queue with focus jobs and non loaded images
        for i, filename in enumerate(self._filenames):
            self._job_queue.put((size + i, (JOB.CALC_FOCUS, filename)))

        for i in range(2, min(self.PRELOAD_RANGE + 1, len(self._filenames))):
            self._job_queue.put((i, (JOB.LOAD_IMAGE, self._filenames[i])))

        self._worker = Worker(self._job_queue, self._images, self._path)
        self._worker.start()
        return True

    def end_worker(self):
        """Stop background worker."""
        if self._worker is None:
            return False

        self._job_queue.put((0, (JOB.EXIT, None)))
        self._worker.join()
        return True


def render_images(left, right):
    """Render given image objects next to each other.

    If heights of both images are different, bigger one is resized.
    """

    imleft = left['image']
    imright = right['image']

    # first resize images to same height
    left_height, left_width, _ = imleft.shape
    right_height, right_width, _ = imright.shape

    if left_height < right_height:
        new_width = int((left_height / right_height) * right_width)
        imright = cv2.resize(imright, (new_width, left_height))
        imleft = imleft.copy()

        right_height, right_width, _ = imright.shape
    else:
        new_width = int((right_height / left_height) * left_width)
        imleft = cv2.resize(imleft, (new_width, right_height))
        imright = imright.copy()

        left_height, left_width, _ = imleft.shape

    # embed focus strings into both images
    cv2.putText(imleft, f"Focus: {left['focus']:.2f}", (50, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), thickness=20)
    cv2.putText(imright, f"Focus: {right['focus']:.2f}", (50, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), thickness=20)

    # embed filename info both images
    cv2.putText(imleft, left['filename'], (50, 280),
                cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), thickness=12)
    cv2.putText(imright, right['filename'], (50, 280),
                cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), thickness=12)

    # merge and display whole image
    image = numpy.hstack((imleft, imright))

    cv2.imshow(WINDOW_NAME, image)
    cv2.waitKey(1)  # needed to display the image


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    parser.add_argument("-i", "--images", required=True,
                        help="path to the directory with images")
    parser.add_argument("-t", "--treshold", default=0,
                        help="focus treshold for auto choosing (default 0)")
    parser.add_argument("-w", "--without-threading", action='store_true',
                        help="disable background preloading")

    args = vars(parser.parse_args())

    filenames = get_images(args['images'])

    if args['verbose']:
        global verbose
        verbose = print

    if not filenames:
        sys.stderr.write("There are no images to display.")
        sys.exit(2)

    try:
        os.mkdir(f"{args['images']}/deleted")
    except FileExistsError:
        pass

    handler = ImageHandler(args['images'], filenames)
    if not args['without_threading']:
        handler.start_worker()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 640)

    rerender = True
    while True:

        if rerender:
            left, right = handler.current
            render_images(left, right)

        rerender = False

        key = -1
        while key == -1:
            key = cv2.waitKey(1000)

        if key == KEYBOARD.LEFT:
            rerender = handler.roll_right()

        elif key == KEYBOARD.RIGHT:
            rerender = handler.roll_left()

        elif key in [KEYBOARD.A, KEYBOARD.D, KEYBOARD.S]:

            if key == KEYBOARD.A:
                filename = handler.left['filename']
                handler.delete_left()

            elif key == KEYBOARD.D:
                filename = handler.right['filename']
                handler.delete_right()

            elif key == KEYBOARD.S:

                difference = handler.left['focus'] - handler.right['focus']

                if abs(difference) < args['treshold']:
                    continue

                elif difference > 0:
                    filename = handler.right['filename']
                    handler.delete_right()
                else:
                    filename = handler.left['filename']
                    handler.delete_left()

            old_path = os.path.join(args['images'], filename)
            new_path = os.path.join(args['images'], "deleted", filename)
            os.rename(old_path, new_path)
            rerender = True

        elif key == KEYBOARD.F:
            if not cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN):
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

        elif key == KEYBOARD.X:
            cv2.destroyWindow(WINDOW_NAME)
            handler.end_worker()
            break

        else:
            verbose(f"Key {key} pressed.")

        if len(handler) < 2:
            cv2.destroyWindow(WINDOW_NAME)
            handler.end_worker()
            break


if __name__ == "__main__":
    main()
