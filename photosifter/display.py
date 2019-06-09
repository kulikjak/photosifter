import enum

import cv2
import numpy


# Maximum amount of images displayed at the same time
MAXIMUM_DISPLAY_SIZE = 6


class BORDER(enum.Enum):
    BLUE = [100, 0, 0]
    GREEN = [0, 100, 0]


class DisplayHandler:

    # Name of the application window
    WINDOW_NAME = "Display Handler"

    def __init__(self):

        self._enable_text_embeding = True
        self._current = None

        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.WINDOW_NAME, 1280, 640)

    def __del__(self):
        cv2.destroyWindow(self.WINDOW_NAME)

    @staticmethod
    def _embed_text(image, focus, filename):
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
            if self._enable_text_embeding:
                self._embed_text(image, obj.focus, obj.filename)

            if complete is None:
                complete = image
            else:
                complete = numpy.hstack((complete, image))

        self._current = complete

        cv2.imshow(self.WINDOW_NAME, complete)
        cv2.waitKey(1)  # needed to display the image
