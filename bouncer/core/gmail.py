# Copyright 2023 Dylan Middendorf
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from base64 import urlsafe_b64encode
from email.message import Message
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.interactive import get_user_credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from typing import Optional

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class Gmail:
    def __init__(self, client_id: str, client_secret: str, refresh_token: Optional[str] = None) -> None:
        if not refresh_token:
            serialized_credentials = (client_id, client_secret)
            self._creds = get_user_credentials(SCOPES, *serialized_credentials)
        else:
            # Create minimal client information for credential authentication
            info = {'client_id': client_id, 'client_secret': client_secret, 'refresh_token': refresh_token}

            # Obtain Google OAuth2 Session Credentials
            self._creds = Credentials.from_authorized_user_info(info, SCOPES)
            self._creds.refresh(Request())  # Refresh to obtain an access token

    @property
    def credentials(self) -> Credentials:
        """The active Google OAuth 2.0 credentials."""
        return self._creds

    def send_message(self, message: Message):
        """Send the specified message utilizing the active credentials."""
        try:
            enc_msg = {'raw': urlsafe_b64encode(message.as_bytes()).decode()}
            service: Resource = build('gmail', 'v1', credentials=self._creds)

            # pylint: disable=E1101
            request = service.users().messages().send(userId="me", body=enc_msg)
            return request.execute()
        except HttpError as err:
            print(f'An error occurred: {err}')
            return None
