# Copyright © 2019 Province of British Columbia
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
"""Exposes all of the resource endpoints mounted in Flask-Blueprints."""

from .callback import bp as callback_bp_v2
from .email_validation import bp as email_validation_bp_v2
from .resend import bp as resend_bp_v2
from .safe_list import bp as safe_list_bp_v2

__all__ = ["callback_bp_v2", "email_validation_bp_v2", "resend_bp_v2", "safe_list_bp_v2"]
