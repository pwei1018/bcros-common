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
"""API endpoint for receiving BC Notify callback events."""

from functools import wraps
import hashlib
import hmac
from http import HTTPStatus
import sys

from flask import Blueprint, current_app, request
from flask_pydantic import validate
from structured_logging import StructuredLogging

from notify_api.models import BCNotifyCallback, BCNotifyCallbackRequest, Notification, NotificationHistory, db
from notify_api.utils.auth import jwt
from notify_api.utils.enums import Role

logger = StructuredLogging.get_logger()
bp = Blueprint("CALLBACK", __name__, url_prefix="/callback")

SIGNATURE_HEADER = "X-Webhook-Signature"


def _signature_is_valid(secret: str) -> bool:
    """Compare the header's sha256=<hex> HMAC with one computed over the raw request body."""
    received = request.headers.get(SIGNATURE_HEADER, "")
    expected = "sha256=" + hmac.new(secret.encode(), request.get_data(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)


def requires_callback_auth(func=None, *, config_key: str = "BC_NOTIFY_WEBHOOK_SECRET"):
    """Authenticate a BC Notify webhook signature when configured, otherwise use JWT roles."""

    def decorator(view_func):
        jwt_protected = jwt.requires_auth(jwt.has_one_of_roles([Role.BC_NOTIFY_CALLBACK.value])(view_func))

        @wraps(view_func)
        def wrapper(*args, **kwargs):
            secret = current_app.config.get(config_key)
            if not secret:
                return jwt_protected(*args, **kwargs)
            if not _signature_is_valid(secret):
                logger.warning("BC Notify callback rejected: invalid webhook signature")
                return {"message": "Invalid webhook signature"}, HTTPStatus.UNAUTHORIZED
            return view_func(*args, **kwargs)

        return wrapper

    return decorator(func) if func is not None else decorator


def process_bc_notify_callback(body: BCNotifyCallbackRequest) -> NotificationHistory | Notification | None:
    """Persist a callback and archive its notification only after successful completion."""
    BCNotifyCallback.save(body)
    response_id = body.data.notify_id
    notification = Notification.find_by_response_id(response_id)

    if notification:
        if body.data.status.lower() not in {"success", "completed"}:
            return notification

        try:
            notification.status_code = Notification.NotificationStatus.DELIVERED
            notification.update_notification(commit=False)
            history = NotificationHistory.create_history(notification, response_id=response_id, commit=False)
            history.notify_status = body.data.status
            notification.delete_notification(commit=False)
            db.session.commit()
            return history
        except Exception:
            db.session.rollback()
            raise

    history = NotificationHistory.find_by_response_id(response_id)
    if history:
        history.notify_status = body.data.status
        history.update()
    return history


@bp.route("/", methods=["POST", "OPTIONS"])
@requires_callback_auth
@validate()
def callback(body: BCNotifyCallbackRequest):  # pylint: disable=unused-argument
    """Persist a BC Notify status event and update its notification history."""
    try:
        process_bc_notify_callback(body)

    except Exception as err:  # pylint: disable=broad-except,unused-variable
        logger.error(f"Callback error: {err}, details: {sys.exc_info()}")
    return {}, HTTPStatus.OK


@bp.route("/housing/", methods=["POST", "OPTIONS"], strict_slashes=False)
@requires_callback_auth(config_key="BC_NOTIFY_HOUSING_WEBHOOK_SECRET")
@validate()
def housing_callback(body: BCNotifyCallbackRequest):  # pylint: disable=unused-argument
    """Persist a BC Notify Housing status event and update its notification history."""
    try:
        process_bc_notify_callback(body)

    except Exception as err:  # pylint: disable=broad-except,unused-variable
        logger.error(f"BC Notify Housing callback error: {err}, details: {sys.exc_info()}")
    return {}, HTTPStatus.OK
