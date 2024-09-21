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

import json
from io import TextIOWrapper
from typing import Optional
from util.singleton import Singleton


class Configuration(metaclass=Singleton):
    _instance: Configuration = None

    def __init__(self, config: TextIOWrapper) -> None:
        self._instance = self  # Cache for improved performance
        self._name, self._data = config.name, json.load(config)

    def __getitem__(self, key):
        return self._data[key]

    @staticmethod
    def instance(config: Optional[TextIOWrapper] = None) -> Configuration:
        inst = Configuration._instance  # increase readability

        if inst is None:  # Ensure configuration has been initialized
            inst = Configuration(config)  # Generate singleton instance
        return inst

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def save(filename: Optional[str] = None) -> None:
        inst = Configuration._instance  # increase readability
        filename = inst.name if filename is None else filename
        with open(filename, "wt") as config:
            json.dump(config, inst._data, indent=2)
