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

            store = file.Storage('credentials.json')
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
                creds = tools.run_flow(flow, store)
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
