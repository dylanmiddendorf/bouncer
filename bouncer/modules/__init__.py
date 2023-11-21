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

from inspect import getmembers, ismethod
from types import MethodType

from discord.app_commands import Command, Group, command

# TODO Check if group/command overlap can occur


class Module:
    @property
    def commands(self):
        def iscommand(method):
            # type: (tuple[str, MethodType]) -> bool
            """Return true if the method is a application command."""
            return method[0] not in whitelist and method[0][0] != '_'
        whitelist = getmembers(Module, ismethod)  # List of inherited methods

        def addcommand(command_tree, name, callback):
            # type: (dict[str, dict | str], str, MethodType) -> None
            """Adds an application command to the tree."""
            for key in name[:-1]:
                command_tree = command_tree.setdefault(key, {})
                assert isinstance(command_tree, dict)
            command_tree[name[-1]] = callback

        def buildcommand(name, callback):
            # type: (str, dict | MethodType) -> Command | Group
            """Constructs an applicaion command from a command tree"""
            if isinstance(callback, MethodType):
                description = callback.__doc__  # Obtain description from docstring
                return command(name=name, description=description)(callback)
            elif isinstance(callback, dict):
                command_group = Group(name=name)  # Initalize command group
                for c in callback.items():
                    command_group.add_command(buildcommand(*c))
                return command_group
            raise ValueError('Invalid type detected within command tree')

        command_tree: dict[str, dict | MethodType] = {}  # Store commands
        for name, callback in filter(iscommand, getmembers(self, ismethod)):
            addcommand(command_tree, name, callback)  # Construct command tree
        return [buildcommand(*c) for c in command_tree.items()]


class ModuleLoader:
    pass
