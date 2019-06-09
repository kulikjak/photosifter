# Photo sifter

Photo sifter is a simple application, written in Python, for smooth photo sifting and comparison. It can work locally as well as (with some additional setup) directly with remote Google Images.

I wrote this because I do often take several photos in quick succession (to reduce the possibility of them being fuzzed) and Google Photos is not the best place to find the best of them. It lacks the ability to display two or more images near each other as well as some arbitrary focus metric, both of which are in this application and help immensely.

Also, it is much faster because there are no unnecessary animations and loading (images are dynamically preloaded in the background).

## Installation and Usage

Simplest way is to install package with pip:
```
pip install photosifter
```

The minimum version of Python runtime is 3.6 (due to the usage of f-Strings).

Start by running `photosifter local <folder>` to sift through the images in a given folder, or run `photosifter guide` to see all modes of operation and app key bindings.

### Remote mode

The first time you use the app in a remote mode, you will be asked to give photosifter a proper authorization to work with your Google photos. The application will remember you, and you won't have to login again next time you use it. If you don't want to be remembered, pass `--forget-user` option to the application (this is important mainly on public machines).

Note that Google Photos API is still young and very limited, and cannot be used directly for deleting images (or even adding them to albums). To get around this limitation, see the `gphotos_deleter` section below. Also, due to this limitation, you won't have to be afraid that something wrong will happen with your images when using this application.

NOTE: If you want to [create](https://developers.google.com/photos/library/guides/get-started#enable-the-api) your own Google Project and use it instead of the supplied one, simply replace the `client_secret.json` file in the `auth` directory with yours. However, be assured that using the supplied project is no less secure than using your own.

### GPhotos_deleter

Each time you use the app in remote mode, JSON file with image URLs of deleted images is created in the application folder. You can either delete images manually or use the `gphotos_deleter` and do so automatically in a way that human would (script starts a browser, and then one by one automatically deletes all images given).

`gphotos_deleter` does so by looking for certain elements on the screen and clicking them. Because it searches for element values which are different for each language, you might need to change them for yours (`DELETE_BUTTON_TITLE` and `CONFIRMATION_TEXT` - both at the top of the script).

Before using it, you will also need to install selenium python package (`pip install selenium`) and download a chrome webdriver from [here](http://chromedriver.chromium.org/downloads). Place chromedriver somewhere in the PATH or explicitly pass it with `--chromedriver` option. After all, is set up, you can start the script with:

```
gphotos_deleter --file yourfile.json
```

The first time you start the deleter, you will be asked to log into your Google Photos (sadly, since this is a different way of authentication, login from here and from `photosifter` cannot be combined into a single one), then deleter will proceed with the deletion. After all, images are deleted, deleter checks that they really are (that is why `404` screens start appearing, so don't worry). If some are still not deleted, it tries to do that once more.

Note that while tested, this way of deleting images is somewhat sketchy so there is a small chance that the wrong one will be deleted (even though I never seen it once during testing). Also, I am not sure how well will it work on slow internet connection (time limits and delays might need to be adjusted for that).

**NOTE:** Once (if ever) Google API allows deletion, I will surely include it here because included `gphotos_deleter`, while cool, is obviously not the best way of doing so.

## Known Issues

Arrow keys can sometimes stop working after pressing `tab` key (not sure why). For that reason, there is a second set of keys with the same functionality (`,` and `.`). Restarting also solves this issue.

## Author

**Jakub Kulik** - [kulikjak](https://github.com/kulikjak)

## License

This project is licensed under the MIT License - see the [LICENSE](https://raw.githubusercontent.com/kulikjak/photosifter/master/LICENSE) file for details

## Links

- [Project repository](https://github.com/kulikjak/photosifter)
- [Pypi page](https://pypi.org/project/photosifter)
