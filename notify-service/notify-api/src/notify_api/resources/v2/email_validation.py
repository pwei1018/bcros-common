# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API endpoints for validate email address."""

from http import HTTPStatus

from flask import Blueprint
from flask_pydantic import validate

from notify_api.models import EmailValidator

bp = Blueprint("EMAIL_VALIDATION", __name__, url_prefix="/email_validation")


@bp.route("/", methods=["GET", "OPTIONS"])
# @jwt.requires_auth
@validate()
def email_validation(query: EmailValidator):  # noqa: ARG001
    """Get notification endpoint by id."""
    return {}, HTTPStatus.OK
