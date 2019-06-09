import enum
import json
import os
import queue
import threading
import time

from collections import deque

from photosifter.util import verbose
from photosifter.image import Image


class JOB(enum.Enum):
    """Enum containing job types for background thread worker."""

    DOWNLOAD_IMAGE = 0
    LOAD_IMAGE = 1
    CALC_FOCUS = 2
    EXIT = 3


class Worker(threading.Thread):
    """Background worker class."""

    def __init__(self, job_queue):
        """Initialize background image preloading thread.

        Args:
            job_queue: priority queue with worker jobs
        """
        threading.Thread.__init__(self)

        self._queue = job_queue
        self._download_capable = False

        self._filenames = None
        self._images = None
        self._path = None
        self._library = None

    def enable_downloading(self, filenames, images, path, library):
        """Enable download capability of the Worker

        To download images and create new Image objects, the worker needs to
        have access to all of these additional arguments. These are not passed
        via the constructor, because they are unnecessary for the local stuff
        and would merely make a list of arguments needlessly big.

        Args:
            filenames: sorted list of image filenames.
            images: main map of Image objects.
            path: download path of all new images.
            library: GooglePhotosLibrary object.
        """
        self._filenames = filenames
        self._images = images
        self._path = path
        self._library = library

        self._download_capable = True

    def run(self):
        """Worker thread run method"""

        while True:
            _, item = self._queue.get()
            job, obj = item

            if obj is not None:
                verbose(f"Background job: {job.name} : {obj.filename}")
            else:
                verbose(f"Background job: {job.name}")

            # stop thread and return back to main one
            if job is JOB.EXIT:
                break

            if job is JOB.DOWNLOAD_IMAGE:
                if not self._download_capable:
                    print("Worker: cannot download if not download capable.")
                    print("Did you forget to call enable_downloading func?")
                    continue

                mediaItem = self._library.get_next()
                filename = mediaItem['filename']

                verbose(f"Background job: {job.name} : {filename}")

                obj = Image(filename, self._path, mediaItem)
                obj.load_image()

                self._images[filename] = obj
                self._filenames.append(filename)

            # preload image itself
            elif job is JOB.LOAD_IMAGE:
                obj.load_image()

            # calculate focus of an image
            elif job is JOB.CALC_FOCUS:
                obj.load_image(focus_only=True)

            else:
                if isinstance(job, JOB):
                    print(f"Worker: Unsupported job: {job.name}")
                else:
                    print(f"Worker: Unknown job: {job}")


class BaseImageHandler:
    """Base class for image carousel handling."""

    PRELOAD_RANGE = 10

    def __init__(self, path, filenames, images, with_threading=True, backup_maxlen=None):
        """Initialize image handler class.

        Args:
            path: path to the directory with images.
            filenames: sorted list of image filenames.
            images: main map of Image objects.
            with_threading: whether to enable background image preloading.
            backup_maxlen: maximum size of the backup queue.

        This class should be subclassed and filenames and images arguments
        initialized in subclass constructors.
        """

        self._idx = 0
        self._worker = None
        self._job_queue = None
        self._backup = deque(maxlen=backup_maxlen)

        self._path = path
        self._filenames = filenames
        self._images = images

        if with_threading:
            self._start_worker()

    def __del__(self):
        if self._worker:
            self._end_worker()

    def __len__(self):
        return len(self._filenames)

    def __getitem__(self, key):
        """Get Image object based on the given key.

        Key can be both integer and string. Integer returns nth Image
        from the list, string retrieves Image with given filename.
        """

        if isinstance(key, int):
            key = self._filenames[key]
        elif not isinstance(key, str):
            raise TypeError("Key must be of instance 'int' or 'str'")

        return self._images[key]

    def get_relative(self, idx):
        """Get Image object with given offset relative to current view."""
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
            self.__getitem__(idx).deload_image()

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
        """Delete image from the carousel.

        Argument 'total' is given to specify the number of currently displayed
        images and is used to determine how should the view move after one
        image is removed.
        """
        idx = self._idx + offset
        try:
            obj = self.__getitem__(idx)
        except IndexError:
            return None

        self._backup.append((idx, obj))

        del self._filenames[idx]
        obj.delete()

        if self._idx > 0 and total / 2 > offset:
            self._idx -= 1
            self._load(self._idx - self.PRELOAD_RANGE)
        else:
            self._load(self._idx + self.PRELOAD_RANGE + 1)

        return obj

    def swap_images(self, first, second):
        self._filenames[self._idx + first], self._filenames[self._idx + second] = \
            self._filenames[self._idx + second], self._filenames[self._idx + first]

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

    def get_list(self, amount):
        """Get 'amount' images from current view."""
        objects = []
        try:
            for i in range(amount):
                objects.append(self.__getitem__(self._idx + i))
        except IndexError:
            pass

        return objects

    def _start_worker(self):
        """Start background worker."""
        self._job_queue = queue.PriorityQueue()
        self._worker = Worker(self._job_queue)
        self._worker.start()

    def _end_worker(self):
        """Stop background worker."""
        self._job_queue.put((0, (JOB.EXIT, None)))
        self._worker.join()


class ImageHandler(BaseImageHandler):

    # All allowed image extensions
    ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.png', '.jpeg')

    def __init__(self, path, with_threading=True, backup_maxlen=None):
        """Initialize image handler class.

        Args:
            path: path to the directory with images.
            with_threading: whether to enable background image preloading.
            backup_maxlen: maximum size of the backup queue.

        This handler is used for locally saved images.

        Class loads all images from the given directory (it is nonrecursive
        meaning that subdirectories are not checked) Images are sorted
        alphabetically and only contains files with allowed extensions.
        """

        files = os.listdir(path)  # Throws IOError
        filenames = [file for file in files if file.endswith(self.ALLOWED_IMAGE_EXTENSIONS)]
        images = {filename: Image(filename, path) for filename in filenames}

        # NOTE: This way of sorting might not be the most efficient, but it works well
        filenames.sort(key=lambda item: item.replace('.', chr(0x01)))

        BaseImageHandler.__init__(self, path, filenames, images, with_threading, backup_maxlen)

    def _start_worker(self):
        """Start background worker."""
        BaseImageHandler._start_worker(self)

        # fill queue with focus jobs and non loaded images
        size = len(self._images)
        for i, filename in enumerate(self._filenames):
            self._job_queue.put((size + i, (JOB.CALC_FOCUS, self.__getitem__(filename))))

        for i in range(2, min(self.PRELOAD_RANGE + 1, len(self._filenames))):
            self._job_queue.put((i, (JOB.LOAD_IMAGE, self.__getitem__(i))))


class RemoteImageHandler(BaseImageHandler):

    def __init__(self, path, library, backup_maxlen=None):
        """Initialize image handler class.

        Args:
            path: path to the directory with images.
            library: GooglePhotosLibrary object.
            backup_maxlen: maximum size of the backup queue.

        This handler is used for remotely saved images.

        Class is periodically downloading images from the Google Photos service
        from newest to oldest. Since the image download is very time-consuming
        operation, it must be done in the background, and thus this handler
        cannot operate without the thread support.
        """

        self._library = library
        filenames = []
        images = {}

        if not os.path.exists(path):
            os.makedirs(path)

        for mediaItem in self._library.get_multiple(10):
            filename = mediaItem['filename']
            filenames.append(filename)

            image = Image(filename, path, mediaItem)
            image.download_image()
            images[filename] = image

        BaseImageHandler.__init__(self, path, filenames, images, True, backup_maxlen)

    def __del__(self):
        BaseImageHandler.__del__(self)

        # Sadly, Google Photos API doesn't support image deletion so we cannot
        # use the API to delete those photos which were removed in this app.
        # Moving images into albums is also not possible, and thus we cannot
        # even create an album with images to delete.
        # The current workaround is to use Selenium based frontend deleter.
        # This part creates a file which can be given to it as an argument.

        deleted = [obj.productUrl for obj in self._images.values() if obj.deleted]
        if deleted:
            filename = f"{time.strftime('%Y%m%d_%H%M%S')}_deleted.json"
            print(f"Generated file for use with gphotos_deleter: {filename}.")

            with open(filename, 'w') as outfile:
                json.dump(deleted, outfile)

    def _start_worker(self):
        """Start background worker."""
        BaseImageHandler._start_worker(self)
        self._worker.enable_downloading(self._filenames, self._images,
                                        self._path, self._library)

        for i in range(2, min(self.PRELOAD_RANGE + 1, len(self._filenames))):
            self._job_queue.put((i, (JOB.LOAD_IMAGE, self.__getitem__(i))))

    def _load(self, idx):
        BaseImageHandler._load(self, idx)

        # Add remote download job if index is out of range on the right side
        if idx > len(self._filenames) - 2:
            verbose(f'Main: download image {idx}')
            self._job_queue.put((10, (JOB.DOWNLOAD_IMAGE, None)))
