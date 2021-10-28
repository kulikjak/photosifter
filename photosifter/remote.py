import os
from argparse import Namespace

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from photosifter.util import AUTH_BASE


# Get absolute paths to auth related files
credentials_file = os.path.join(AUTH_BASE, "token.json")
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
            SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

            creds = None
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists(credentials_file):
                creds = Credentials.from_authorized_user_file(credentials_file, SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
                    creds = flow.run_local_server()
                # Save the credentials for the next run
                with open(credentials_file, 'w') as token:
                    token.write(creds.to_json())

            return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

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
