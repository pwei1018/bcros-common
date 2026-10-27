# Copyright © 2026 Province of British Columbia
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
"""API endpoint for sending SMS notifications through BC Notify."""

from http import HTTPStatus

from flask import Blueprint, jsonify
from flask_pydantic import validate

from notify_api.models import SmsRequest
from notify_api.services import notify
from notify_api.utils.auth import jwt
from notify_api.utils.enums import Role

bp = Blueprint("SMS", __name__, url_prefix="/sms")


@bp.route("", methods=["POST"])
@jwt.requires_auth
@jwt.has_one_of_roles([Role.SYSTEM.value, Role.PUBLIC_USER.value, Role.STAFF.value])
@validate()
def send_sms(body: SmsRequest):
    """Create and send SMS notification endpoint."""
    notification = notify.queue_publish_sms(body)
    # The delivery service may archive the row before we respond; fall back to the cached response.
    try:
        response = notification.json
    except Exception:
        response = getattr(notification, "_cached_response", {"id": None, "notifyStatus": "QUEUED"})
    return jsonify(response), HTTPStatus.OK
