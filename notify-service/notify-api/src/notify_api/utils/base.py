# Copyright © 2021 Province of British Columbia
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
"""This module holds all of the basic data about a business."""

from enum import EnumMeta, StrEnum
from typing import Any


class BaseMeta(EnumMeta):
    """Meta class for the enum."""

    def __contains__(cls, other):  # pylint: disable=C0203
        """Return True if 'in' the Enum."""
        try:
            cls(other)  # pylint: disable=no-value-for-parameter
        except ValueError:
            return False
        else:
            return True


class BaseEnum(StrEnum, metaclass=BaseMeta):
    """Replace autoname from Enum class."""

    def __str__(self):
        """Return the string value of the Enum."""
        return str(self.value)

    @classmethod
    def get_enum_by_value(cls, value: str) -> str | None:
        """Return the enum by value."""
        for enum_value in cls:
            if enum_value.value == value:
                return enum_value
        return None

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> str:  # noqa: ARG004
        """Return the lower-cased version of the member name."""
        return name.lower()
