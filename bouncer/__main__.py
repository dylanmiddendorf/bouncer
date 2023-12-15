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

import asyncio
import os
from argparse import ArgumentParser, FileType
from discord import Intents
from discord.ext.commands.bot import Bot
from core.config import Configuration
from core.gmail import Gmail
from modules.verification import Verificiation

DEFAULT_CONFIG_FILE = os.path.join('templates', 'configuration.json')

def main():
    parser = ArgumentParser()  # Quickly parse arguments (if any)
    parser.add_argument('--config', nargs='?', default=DEFAULT_CONFIG_FILE,
                        type=FileType('r'), help='Configuration file path')
    args = parser.parse_args()
    config = Configuration(args.config)

    # Load and deserialize relevent credentials
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
    gmail_client = Gmail(client_id, client_secret, refresh_token)

    # Update the cache the refresh token (for future use)
    if not refresh_token:
        refresh_token = gmail_client.credentials.refresh_token
        os.environ['GOOGLE_REFRESH_TOKEN'] = refresh_token

    # Start the discord client
    bouncer = Bot('!', intents=Intents.all())
    asyncio.run(bouncer.add_cog(Verificiation(config, gmail_client)))

    @bouncer.event
    async def on_ready():
        await bouncer.tree.sync()

    bouncer.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    main()
