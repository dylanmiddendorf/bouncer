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

"""Python module for implementing the singleton design pattern."""


class Singleton(type):
    """
    Metaclass for implementing the Singleton design pattern.

    This metaclass ensures that a class can have only one instance. When a new
    instance is requested, it checks if an instance of the class already
    exists, and if it does, it returns the existing instance. If not, it
    creates a new instance and stores it for future use.

    Example:
        ```py
        SingletonImpl = type('SingletonImpl', (Singleton), {})
        s, p = SingletonImpl(), SingletonImpl()
        assert s == p # Ensure all instances are syncronized
        ```
    See Also:
        https://stackoverflow.com/a/6798042
   """

    _instances = {}  # Maps types to their associated instances

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
