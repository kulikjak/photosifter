import os
from urllib.request import urlopen

import cv2


class Image:

    def __init__(self, filename, path, mediaItem=None):

        self._mediaItem = mediaItem
        self._filename = filename
        self._path = path

        self._downloaded = os.path.isfile(os.path.join(path, filename))
        self._deleted = False
        self._focus = None
        self._base_image = None
        self._image_map = {}

    def __lt__(self, other):
        """Note: This comparator is here to keep deque from throwing type errors
        when two objects with the same priority are given. We don't really care
        which one of them will be processed first, so no real comparison occurs.
        """
        return True

    def download_image(self):
        if self._downloaded:
            return

        with urlopen(f"{self._mediaItem['baseUrl']}=d") as src:
            with open(os.path.join(self._path, self._mediaItem['filename']), 'wb') as dst:
                dst.write(src.read())
        self._downloaded = True

    def load_image(self, focus_only: bool = False):
        """Load image into the application memory.

        If focus_only is True, the image itself is not saved and only focus
        is calculated. Image is not deloaded if it was already saved.
        """

        def _load_image(path, filename):
            """Get image object or None from given path and filename."""
            return cv2.imread(os.path.join(path, filename))

        def _get_image_focus(image):
            """Get focus value of given image."""
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return cv2.Laplacian(gray, cv2.CV_64F).var()

        # Download image if it is not yet downloaded
        if not self._downloaded:
            self.download_image()

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
        """Deload image (in all sizes) from the application memory"""
        self._base_image = None
        self._image_map = {}

    def get(self, height=None):
        """Get image itself, optionally with specified height.

        If the optional height is given, the image is resized to a given
        height and also cached for possible later use.

        If the image itself exists, this method is guaranteed to succeed
        no matter of the current state object (download and load are
        done if necessary).
        """

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
        """Delete the image in the context of the application.

        This is done by setting this object into the deleted state a moving
        the image itself into backup 'deleted' folder. Image is also deloaded
        to restore some memory.

        Does nothing for already deleted images.
        """

        if self._deleted or not self._downloaded:
            return

        self._deleted = True
        self.deload_image()

        old_file = os.path.join(self._path, self._filename)
        self._path = os.path.join(self._path, "deleted")
        new_file = os.path.join(self._path, self._filename)
        os.rename(old_file, new_file)

    def restore(self):
        """Restore previously deleted image in the context of the application.

        This is the reversal of the delete method with one difference that
        images are not loaded back into the memory (due to the fact that image
        restoration can occur out of the view).

        Does nothing for non deleted images.
        """

        if not self._deleted or not self._downloaded:
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

    @property
    def mediaItem(self):
        return self._mediaItem

    @property
    def productUrl(self):
        if self._mediaItem and 'productUrl' in self._mediaItem:
            return self._mediaItem['productUrl']
        return None
