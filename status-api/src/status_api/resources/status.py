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
"""Resource for Service status endpoints."""
from http import HTTPStatus

from arrow import Arrow
from flask import Blueprint, jsonify
from flask_cors import cross_origin

from status_api.services.status import Status as StatusService

bp = Blueprint("STATUS", __name__, url_prefix="/")

STATUS_SERVICE = StatusService()


@bp.route("/status/<string:service_name>", methods=["GET"])
@cross_origin(origin="*")
def get(service_name: str):
    """Get the service schedule and return status and next schedule date/time."""
    response, status = (
        STATUS_SERVICE.check_status(service_name, Arrow.utcnow()),
        HTTPStatus.OK,
    )
    return jsonify(response), status
