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
"""Exposes all of the resource endpoints mounted in Flask-Blueprint style."""
from flask import Flask

from status_api.resources.meta import bp as meta_bp
from status_api.resources.ops import bp as ops_bp
from status_api.resources.status import bp as status_bp
from status_api.resources.whatsnew import bp as whatsnew_bp


def register_endpoints(app: Flask):
    """Register endpoints with the flask application."""
    # Allow base route to match with, and without a trailing slash
    app.url_map.strict_slashes = False

    app.register_blueprint(meta_bp)
    app.register_blueprint(ops_bp)
    app.register_blueprint(status_bp, url_prefix="/api/v1")
    app.register_blueprint(whatsnew_bp, url_prefix="/api/v1")
