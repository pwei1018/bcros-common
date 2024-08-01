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
"""Endpoints to check and manage the health of the service."""
from flask import Blueprint

bp = Blueprint("OPS", __name__, url_prefix="/ops")


@bp.route("/healthz")
def healthz():
    """Determine if the service and required dependencies are still working."""
    # made it here, so all checks passed
    return {"message": "api is healthy"}, 200


@bp.route("/readyz")
def readyz():
    """Return a JSON object that identifies if the service is setupAnd ready to work."""
    return {"message": "api is ready"}, 200
