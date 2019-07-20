import os
from argparse import Namespace

from apiclient.discovery import build  # pylint: disable=E0401
from httplib2 import Http
from oauth2client import client, file, tools

from photosifter.util import AUTH_BASE


# Get absolute paths to auth related files
credentials_file = os.path.join(AUTH_BASE, "credentials.json")
client_secret_file = os.path.join(AUTH_BASE, "client_secret.json")


def forget_credentials():
    if os.path.isfile(credentials_file):
        print("Forgetting current user")
        os.remove(credentials_file)


class GooglePhotosLibrary:

    # This is the maximum size that Google Photos API allows.
    PAGE_SIZE = 100

    def __init__(self):

        def get_photos_service():
            # Request read and write access without the sharing one
            SCOPES = 'https://www.googleapis.com/auth/photoslibrary'

            # If credentials file doesn't exist, create it to prevert warnings
            if not os.path.isfile(credentials_file):
                open(credentials_file, 'a').close()

            store = file.Storage(credentials_file)
            creds = store.get()
            if not creds or creds.invalid:

                # Check that client_server file exists
                if not os.path.isfile(client_secret_file):
                    raise OSError(2, "No such file or directory", "client_secret.json")

                flow = client.flow_from_clientsecrets(client_secret_file, SCOPES)
                args = Namespace(logging_level='ERROR',
                                 auth_host_name='localhost',
                                 noauth_local_webserver=False,
                                 auth_host_port=[8000, 8090])
                creds = tools.run_flow(flow, store, args)
            return build('photoslibrary', 'v1', http=creds.authorize(Http()))

        self._previous = None
        self._service = get_photos_service()
        self._results = self._service.mediaItems().list(pageSize=self.PAGE_SIZE).execute()

    def get_next(self):
        while True:
            while 'mediaItems' not in self._results or not self._results['mediaItems']:
                # nextPageToken can be missing but I have so many photos.....
                self._results = self._service.mediaItems().list(
                    pageSize=self.PAGE_SIZE,
                    pageToken=self._results['nextPageToken']).execute()

            mediaItem = self._results['mediaItems'][0]
            del self._results['mediaItems'][:1]

            # This is an image file
            if 'photo' in mediaItem['mediaMetadata']:
                # We cannot process gif files
                if mediaItem['mimeType'] == 'image/gif':
                    continue

                self._previous = mediaItem['id']
                return mediaItem

    def get_multiple(self, amount):
        return [self.get_next() for _ in range(amount)]

    def create_album(self, title):
        # This is unused due to the problem in add_to_album
        return self._service.albums().create(body={"album": {"title": title}}).execute()

    def add_to_album(self, albumId, mediaItemIds):
        # There are currently endpoints to add photographs into an album, but
        # those photographs must be uploaded via the same app, which makes it
        # basically useless. This will hopefully work in the future.
        pass
