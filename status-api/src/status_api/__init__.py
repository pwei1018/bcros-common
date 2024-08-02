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
"""The Status API service.

This module is the API for the BC Registries Status application.
"""
import os

from flask import Flask
from flask_cors import CORS

from status_api import errorhandlers
from status_api.config import config
from status_api.metadata import APP_RUNNING_ENVIRONMENT
from status_api.resources import register_endpoints
from status_api.utils.logging import setup_logging

setup_logging(os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging.yaml"))  # important to do this first


def create_app(service_environment=APP_RUNNING_ENVIRONMENT, **kwargs):
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config[service_environment])
    app.url_map.strict_slashes = False

    CORS(app, resources="*")
    errorhandlers.init_app(app)

    register_endpoints(app)

    return app
