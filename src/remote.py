import os
from argparse import Namespace

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

# Suppress variable naming warning as those are chosen to
# remain consistent with the Google Photos API.
# pylint: disable=C0103


class GooglePhotosLibrary:

    def __init__(self):

        def get_photos_service():
            # Request read and write access without the sharing one
            SCOPES = 'https://www.googleapis.com/auth/photoslibrary'

            # If credentials file doesn't exist, create it to prevert warnings
            if not os.path.isfile('credentials.json'):
                open('credentials.json', 'a').close()

            store = file.Storage('credentials.json')
            creds = store.get()
            if not creds or creds.invalid:

                # Check that client_server file exists
                if not os.path.isfile('client_secret.json'):
                    raise OSError(2, "No such file or directory", "client_secret.json")

                flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
                args = Namespace(logging_level='ERROR',
                                 auth_host_name='localhost',
                                 noauth_local_webserver=False,
                                 auth_host_port=[8000, 8090])
                creds = tools.run_flow(flow, store, args)
            return build('photoslibrary', 'v1', http=creds.authorize(Http()))

        self._service = get_photos_service()
        self._results = self._service.mediaItems().list(pageSize=10).execute()

    def get_next(self):
        while True:
            if not self._results['mediaItems']:
                # nextPageToken can be missing but I have so many photos.....
                self._results = self._service.mediaItems().list(
                    pageSize=10,
                    pageToken=self._results['nextPageToken']).execute()

            mediaItem = self._results['mediaItems'][0]
            del self._results['mediaItems'][:1]

            # This is an image file
            if 'photo' in mediaItem['mediaMetadata']:
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
