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
from .constants import EndpointVersionPath
from .meta import meta_bp
from .ops import ops_bp
from .v1 import business_bp, document_bp, mhr_bp, nr_bp, ppr_bp, report_bp, search_bp
from .version_endpoint import VersionEndpoint

meta_endpoint = VersionEndpoint(
    name="META", path=EndpointVersionPath.META, bps=[meta_bp]
)  # pylint: disable=invalid-name

ops_endpoint = VersionEndpoint(name="OPS", path=EndpointVersionPath.OPS, bps=[ops_bp])  # pylint: disable=invalid-name

v1_endpoint = VersionEndpoint(  # pylint: disable=invalid-name
    name="API_V1",
    path=EndpointVersionPath.API_V1,
    bps=[business_bp, document_bp, mhr_bp, nr_bp, ppr_bp, report_bp, search_bp]
)

TRACING_EXCLUED_URLS = [
    "/meta",
    "/ops"
]
