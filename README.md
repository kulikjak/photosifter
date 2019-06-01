# Photo sifter

Photo sifter is a simple application, written in Python, for smooth photo sifting and comparison. It can work locally as well as (with some additional setup) directly with remote Google Images.

I wrote this because I do often take several photos in quick succession (to reduce the possibility of them being fuzzed) and Google Photos is not the best place to find the best of them. It lacks the ability to display two or more images near each other as well as some arbitrary focus metric, both of which are in this application and help immensely.

Also, it is much faster because there are no unnecessary animations and loading (images are dynamically preloaded in the background).

## Installation and Usage

To install all the dependencies, simply run:
```
pip install -r requirements.txt
```
Only `numpy` and `opencv-python` are needed to work locally, other requirements are for the remote mode.

The minimum version of Python runtime is 3.6 (due to the usage of f-Strings).

Start by running `photosifter.py local <folder>` to sift through the images in a given folder, or run `photosifter.py guide` to see all modes of operation and app key bindings.

### Setting up the remote mode

To run in the remote mode, you need to create a new Google Project and enable Google Photos API. To do so, go [here](https://developers.google.com/photos/library/guides/get-started#enable-the-api), click the big `ENABLE THE GOOGLE PHOTOS LIBRARY API` button and follow the instructions.

* Create a new project (the name is not important)
* Set product name (again, not relevant)
* Where are you calling from? - `Other`

After that, download client configuration, rename it to `client_secret.json` and place it into the application root folder.

The first time you use the app in a remote mode, you will be asked to give your newly created project a proper authorization to work with your images. Note that Google Photos API is very limited, and cannot be used directly for deleting images or adding them to albums. To get around this limitation, see the `frontend_deleter` below.

### Frontend_deleter

Each time you use the app in remote mode, JSON file with image URLs of deleted images is created in the application folder. You can either delete images manually or use the `frontend_deleter` application and do so automatically. It starts a browser, and then one by one automatically deletes all images given. Since Google Photos API cannot be used to delete or manipulate images, this is the only option - to do it as a human would do.

`frontend_deleter` does so by looking for certain elements on the screen and clicking them. Because it searches for element values which are different for each language, you will need to change them for yours (`DELETE_BUTTON_TITLE` and `CONFIRMATION_TEXT` - both at the top of the script).

Before using it, you will also need to install selenium python package (`pip install selenium`) and download a chrome webdriver from [here](http://chromedriver.chromium.org/downloads). After all, is set up, you can start the script with:

```
frontend_deleter.py --file yourfile.json
```

The first time you start the deleter, you will be asked to log into your Google Photos (sadly, since this is a different way of authentication, login from here and from `photosifter` cannot be combined into a single one), then deleter will proceed with the deletion. After all, images are deleted, deleter checks that they really are (that is why `404` screens start appearing, so don't worry). If some are still not deleted, it tries to do that once more.

Note that while tested, this way of deleting images is somewhat sketchy so there is a small chance that the wrong one will be deleted (even though I never seen it once during testing). Also, I am not sure how well will it work on slow internet connection (time limits and delays might need to be adjusted for that).

**NOTE:** Once (if ever) Google API allows deletion, I will surely include it here because included `fontend_deleter`, while cool, is obviously not the best way of doing so.

## Known Issues

Arrow keys can sometimes stop working after pressing `tab` key (not sure why). For that reason, there is a second set of keys with the same functionality (`,` and `.`). Restarting also solves this issue.

`client_secret.json` and other files must be handled better (right now they must be in `cwd`, which is not good)

## Author

**Jakub Kulik** - [kulikjak](https://github.com/kulikjak)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
