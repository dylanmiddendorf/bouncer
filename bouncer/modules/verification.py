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

from __future__ import annotations
from typing import Optional, cast
import re
import secrets
import time
import string

from email.mime.text import MIMEText
from threading import Thread

from discord import Interaction, TextChannel
from discord.app_commands import command
from discord.ext.commands.cog import GroupCog
from discord.ui import View, Button, Modal, TextInput
from discord.utils import MISSING

from core.config import Configuration
from core.gmail import Gmail


VERIFICIATION_MESSAGE = """**Welcome to Our Server! 🎉**

To get started and ensure a safe community, please verify your email through the buttons below.
Once you've verified your email, you'll be all set to explore and engage with our awesome community.
If you have any questions or need assistance, feel free to reach out to our moderators.

Enjoy your time here! 🌟"""


class AuthenticationCode:
    def __init__(self, code: int, max_attempts: int, timeout: int) -> None:
        self._code = code
        self._expires = time.time() + timeout
        self._max_attempts = max_attempts
        self._attempts = 0

    def is_expired(self) -> bool:
        """Returns true if the code has expired."""
        if self._attempts > self._max_attempts:
            return True
        return time.time() > self._expires

    def validate(self, code: int) -> bool:
        self._attempts += 1  # Each validation counts as an attempt
        return False if self.is_expired() else code == self._code


class SendEmailModal(Modal, title="Email Registration"):
    def __init__(self, verification: Verification) -> None:
        super().__init__()  # Continue with modal initialization
        self.verification = verification

    answer = TextInput(label="What is your university email address?")

    async def on_submit(self, interaction: Interaction) -> None:
        email = str(self.answer)
        response, user = interaction.response, interaction.user

        for role in user.roles:
            if role.id in self.verification.roles.values():
                return await response.send_message("You are already authenticated.", ephemeral=True)
        if re.fullmatch(r"(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", email) is None:
            return await response.send_message("Please enter a valid email address.", ephemeral=True)

        domain = email.split("@")[1]
        if not domain in self.verification.roles:
            return await response.send_message("Email domain is not recognized.", ephemeral=True)

        if len(self.verification.codes) > int(self.verification.config["bandwidth"]):
            return await response.send_message(
                "Max verification codes reached, please try again in a few minutes.", ephemeral=True
            )

        # Gather relevant information needed within the email
        code = secrets.randbelow(1_000_000)

        # Build the email's body from verification template
        body = string.Template(self.verification.verification_template)
        body = body.substitute(code=("%06d" % code), username=user.name)

        # Construct the verification email
        msg = MIMEText(body, "html")
        msg["To"], msg["Subject"] = email, "Discord Verification Code"
        self.verification.gmail.send_message(msg)

        gc_args = (user.id, self.verification.config["timeout"])
        Thread(target=self.verification._garbage_collector, args=gc_args).start()

        attempts = self.verification.config["attempts"]
        authentication_code = AuthenticationCode(
            code, attempts, self.verification.timeout
        )
        self.verification.codes[user.id] = (authentication_code, domain)
        await response.send_message("Verification email has been sent!", ephemeral=True)


class VerifyCodeModal(Modal, title="Code Verification"):
    answer = TextInput(label="What is the code provided within the email?")

    def __init__(self, verification: Verification) -> None:
        super().__init__()  # Continue with modal initialization
        self.verification = verification

    async def on_submit(self, interaction: Interaction) -> None:
        user, response = interaction.user, interaction.response

        if user.id not in self.verification.codes:
            return await response.send_message("Please enter your email first.", ephemeral=True)

        role = self.verification.roles[self.verification.codes[user.id][1]]
        if not self.verification.codes[user.id][0].validate(int(str(self.answer))):
            if self.verification.codes[user.id][0].is_expired():
                del self.verification.codes[user.id]
            msg = "An invalid code has been detected, please try again."
            return await response.send_message(msg, ephemeral=True)

        del self.verification.codes[user.id]
        await user.add_roles(interaction.guild.get_role(role))
        await response.send_message("User has been authenticated!", ephemeral=True)


class Verification(GroupCog, group_name="verification"):
    def __init__(self, config: Configuration, gmail: Gmail) -> None:
        self.gmail = gmail
        self.codes: dict[int, tuple[AuthenticationCode, str]] = {}

        self.config = config["authentication"]
        self.bandwidth = self.config["bandwidth"]
        self.timeout = self.config["timeout"]

        template_path = self.config["template"]
        with open(template_path, "rt", encoding="utf-8") as template_file:
            self.verification_template = template_file.read()

        self.roles = self.config["role_associations"]

    @command(name="create")
    async def verification_create(
        self, interaction: Interaction, channel: TextChannel
    ) -> None:
        """Creates new verification system."""
        # Used to construct `send email` & `verify code`
        view = View(timeout=None)
        send_email = Button(label="Send Email", emoji="📧")
        send_email.callback = self._send_email
        view.add_item(send_email)

        verify_code = Button(label="Verify Code", emoji="✅")
        verify_code.callback = self._verify_code
        view.add_item(verify_code)
        await channel.send(VERIFICIATION_MESSAGE, view=view)

        # Provide the user with a generic response
        response = f"Verification system has been created in <#{channel.id}>"
        await interaction.response.send_message(response)

    async def _send_email(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(SendEmailModal(self))

    async def _verify_code(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(VerifyCodeModal(self))

    def _garbage_collector(self, user_id: int, ttl: float):
        """Removes the user id from active codes after the specified ttl."""
        # Delete thread if code has been removed
        time.sleep(ttl + 0.25)  # Sleep until after code expiration
        if user_id in self.codes:
            code = self.codes[user_id][0]
            if code.is_expired():
                del self.codes[user_id]
            else:
                self._garbage_collector(user_id, code._expires - time.time())
