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
"""All of the configuration for the service is captured here.

All items are loaded, or have Constants defined here that
are loaded into the Flask configuration.
All modules and lookups get their configuration from the
Flask config, rather than reading environment variables directly
or by accessing this configuration directly.
"""
import json
import os


class Config:  # pylint: disable=too-few-public-methods
    """Config object."""

    DEBUG = False
    TESTING = False
    DEVELOPMENT = False

    DEPLOYMENT_PLATFORM = os.getenv("DEPLOYMENT_PLATFORM", "OCP")

    SERVICE_SCHEDULE = os.getenv("SERVICE_SCHEDULE")
    PAYBC_OUTAGE_MESSAGE = os.getenv("PAYBC_OUTAGE_MESSAGE")
    WHATSNEW = os.getenv("WHATSNEW")


class ProductionConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for production environment."""

    DEBUG = False


class SandboxConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for sandbox environment."""

    DEBUG = False


class TestingConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for testing(staging) environment."""

    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for development environment."""

    DEVELOPMENT = True
    DEBUG = True


class UnitTestingConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for unit testing environment."""

    TESTING = True
    DEBUG = True
    DEPLOYMENT_PLATFORM = "OCP"

    schedule_json = [
        {
            "service_name": "PAYBC",
            "available": [
                {"dayofweek": "1", "from": "6:00", "to": "21:00"},
                {"dayofweek": "2", "from": "6:00", "to": "21:00"},
                {"dayofweek": "3", "from": "6:00", "to": "21:00"},
                {"dayofweek": "4", "from": "6:00", "to": "21:00"},
                {"dayofweek": "5", "from": "6:00", "to": "21:00"},
                {"dayofweek": "6", "from": "6:30", "to": "21:00"},
                {"dayofweek": "7", "from": "6:30", "to": "21:00"},
            ],
            "outage": [{"start": "2019-11-05 10:00", "end": "2019-11-05 10:10"}],
            "custom": {
                "start": "2021-06-10 09:57",
                "end": "2021-06-12 06:00",
                "message": "TEST - Credit card payments will be unavailable for cooperative and benefit company filings\
                from 9:00 PM September 4th until 6:00 AM September 8th. We apologize for the inconvenience.",
            },
        }
    ]

    SERVICE_SCHEDULE = json.dumps(schedule_json)
    PAYBC_OUTAGE_MESSAGE = "Test"
    WHATSNEW = json.dumps(
        [
            {
                "id": 1,
                "date": "2022-01-01",
                "labels": "New Feature",
                "title": "Modernization Update",
                "description": "<p><p>Hey there, </p> \
                                <p>We introduce a new sign-in flow to let you log in</p> \
                                <p>with BC services card. This will help you keep track</p> \
                                <p>of this and that more effectively.</p> \
                                <ul>\
                                <li>Business Dashboard</li>\
                                <li>Name Request</li>\
                                <li>PPR</li> \
                                </ul> \
                                <p><b>Please check it out! </b></p>",
                "app": "ALL",
                "priority": True,
                "read": False,
            },
            {
                "id": 2,
                "date": "2022-01-03",
                "labels": "Improvement",
                "title": "Modernization Update",
                "description": "<p><p>Hey there, </p> \
                                <p>We intro Starting and managing Benefit</p> \
                                <p>Companies, Cooperative Associations and Name</p>\
                                <p>Requests. BC OnLine will continue to be used</p>\
                                <p>for all other applications.</p>",
                "app": "ALL",
                "priority": False,
                "read": False,
            },
            {
                "id": 3,
                "date": "2022-01-19",
                "labels": "Announcement",
                "title": "Coming soon",
                "description": "<ul>\
                                <li>Wills Search and Registration - 2021 </li>\
                                <li>Personal Property Registry - 2022</li>\
                                <li>OneStop Sole Proprietorship, General Partnership Registrations and maintenance \
                                    filings - 2022</li> \
                                <li>Stages so users can track progress</li> \
                                </ul>",
                "app": "ALL",
                "priority": False,
                "read": False,
            },
            {
                "id": 4,
                "date": "2022-02-19",
                "labels": "Announcement",
                "title": "Coming soon",
                "description": "<ul>\
                                <li>Wills Search and Registration - 2021 </li>\
                                <li>Personal Property Registry - 2022</li>\
                                <li>OneStop Sole Proprietorship, General Partnership Registrations and maintenance \
                                    filings - 2022</li> \
                                <li>Stages so users can track progress</li> \
                                </ul>",
                "app": "ALL",
                "priority": True,
                "read": False,
            },
        ]
    )


config = {
    "development": DevelopmentConfig,
    "test": TestingConfig,
    "sandbox": SandboxConfig,
    "production": ProductionConfig,
    "unitTesting": UnitTestingConfig,
}
