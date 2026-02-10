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
"""This manages all of the authentication and authorization service."""
from http import HTTPStatus
from typing import List

from flask import current_app
from flask_jwt_oidc import JwtManager
from requests import Session, exceptions
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from doc_api.utils.logging import logger

SYSTEM_ROLE = "system"
STAFF_ROLE = "staff"  # Share single role/account id with ppr for search, registration history.
PPR_STAFF_ROLE = "ppr_staff"  # Share single role/account id with ppr for search, registration history.
COLIN_ROLE = "colin"
MHR_ROLE = "mhr"
BC_REGISTRY = "default-roles-bcregistry"
VIEW = "view"
BASIC_USER = "basic"
PRO_DATA_USER = "pro_data"
PUBLIC_USER = "public_user"
USER_ORGS_PATH = "users/orgs"
GOV_ACCOUNT_ROLE = "gov_account_user"
BCOL_HELP_ROLE = "mhr_helpdesk"
BCOL_HELP_ACCOUNT = "helpdesk"
ASSETS_HELP = "helpdesk"  # Share single account id for search, registration history.


def authorized(identifier: str, jwt: JwtManager) -> bool:
    """Verify the user is authorized to submit the request by inspecting the web token.

    The gateway has already verified the JWT with the OIDC service.
    """
    if not jwt:
        return False

    # Could call the auth api here to check the token roles (/api/v1/orgs/{account_id}/authorizations),
    # but JWTManager.validate_roles does the same thing.

    # Basically verify token, the gateway checks products and verifies the JWT.
    if (
        jwt.validate_roles([STAFF_ROLE])
        or jwt.validate_roles([PPR_STAFF_ROLE])
        or jwt.validate_roles([VIEW])
        or jwt.validate_roles([BASIC_USER])
        or jwt.validate_roles([BC_REGISTRY])
    ):
        return True

    #        template_url = current_app.config.get('AUTH_SVC_URL')
    #        auth_url = template_url.format(**vars())

    #        token = jwt.get_token_auth_header()
    #        headers = {'Authorization': 'Bearer ' + token}
    #        try:
    #            http = Session()
    #            retries = Retry(total=5,
    #                            backoff_factor=0.1,
    #                            status_forcelist=[500, 502, 503, 504])
    #            http.mount('http://', HTTPAdapter(max_retries=retries))
    #            rv = http.get(url=auth_url, headers=headers)

    #           if rv.status_code != HTTPStatus.OK \
    #                    or not rv.json().get('roles'):
    #                return False

    #            if all(elem.lower() in rv.json().get('roles') for elem in action):
    #                return True

    #        except (exceptions.ConnectionError,  # pylint: disable=broad-except
    #                exceptions.Timeout,
    #                ValueError,
    #                Exception) as err:
    #            logger.error(f'template_url {template_url}, svc:{auth_url}')
    #            logger.error(f'Authorization connection failure for {identifier}, using svc:{auth_url}', err)
    #            return False

    return False


def authorized_role(jwt: JwtManager, user_role: str) -> bool:
    """Verify the user is authorized to submit a request by inspecting the web token."""
    if jwt.validate_roles([STAFF_ROLE]) or jwt.validate_roles([user_role]):
        return True
    return False


def authorized_token(  # pylint: disable=too-many-return-statements
    identifier: str, jwt: JwtManager, action: List[str]
) -> bool:
    """Assert that the user is authorized to submit API requests for a particular action."""
    if not action or not identifier or not jwt:
        return False

    # All users including staff must have the PPR role.
    if (
        jwt.validate_roles([STAFF_ROLE])
        or jwt.validate_roles([PPR_STAFF_ROLE])
        or jwt.validate_roles([VIEW])
        or jwt.validate_roles([BASIC_USER])
        or jwt.validate_roles([BC_REGISTRY])
    ):
        return True

    if jwt.has_one_of_roles([BASIC_USER, PRO_DATA_USER]):

        template_url = current_app.config.get("AUTH_SVC_URL")
        auth_url = template_url.format(**vars())

        token = jwt.get_token_auth_header()
        headers = {"Authorization": "Bearer " + token}
        try:
            with Session() as http:
                retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
                http.mount("http://", HTTPAdapter(max_retries=retries))
                rv = http.get(url=auth_url, headers=headers)

                if rv.status_code != HTTPStatus.OK or not rv.json().get("roles"):
                    return False

                if all(elem.lower() in rv.json().get("roles") for elem in action):
                    return True

        except (
            exceptions.ConnectionError,  # pylint: disable=broad-except
            exceptions.Timeout,
            ValueError,
            Exception,
        ) as err:
            logger.error(f"template_url {template_url}, svc:{auth_url}")
            logger.error(f"Authorization connection failure for {identifier}, using svc:{auth_url}", err)
            return False

    return False


def user_orgs(token: str) -> dict:
    """Auth API call to get user organizations for the user identified by the token."""
    response = None
    if not token:
        return response

    service_url = current_app.config.get("AUTH_SVC_URL")
    api_url = service_url + "/" if service_url[-1] != "/" else service_url
    api_url += USER_ORGS_PATH

    try:
        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        # logger.debug('Auth get user orgs url=' + url)
        with Session() as http:
            retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
            http.mount("http://", HTTPAdapter(max_retries=retries))
            ret_val = http.get(url=api_url, headers=headers)
            logger.debug("Auth get user orgs response status: " + str(ret_val.status_code))
            # logger.debug('Auth get user orgs response data:')
            response = ret_val.json()
            # logger.debug(response)
    except (
        exceptions.ConnectionError,  # pylint: disable=broad-except
        exceptions.Timeout,
        ValueError,
        Exception,
    ) as err:
        logger.error(f"Authorization connection failure using svc:{api_url}", err)

    return response


def account_org(token: str, account_id: str) -> dict:
    """Auth API call to get the account organization info identified by the account id."""
    response = None
    if not token or not account_id:
        return response

    service_url = current_app.config.get("AUTH_SVC_URL")
    api_url = service_url + "/" if service_url[-1] != "/" else service_url
    api_url += f"orgs/{account_id}"

    try:
        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        # logger.debug('Auth get user orgs url=' + url)
        with Session() as http:
            retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
            http.mount("http://", HTTPAdapter(max_retries=retries))
            ret_val = http.get(url=api_url, headers=headers)
            logger.debug("Auth get user orgs response status: " + str(ret_val.status_code))
            # logger.debug('Auth get account org response data:')
            response = ret_val.json()
            # logger.debug(response)
    except (
        exceptions.ConnectionError,  # pylint: disable=broad-except
        exceptions.Timeout,
        ValueError,
        Exception,
    ) as err:
        logger.error(f"Authorization connection failure using svc:{api_url}", err)

    return response


def is_staff(jwt: JwtManager) -> bool:
    """Return True if the user has the BC Registries staff role."""
    if not jwt:
        return False
    if jwt.validate_roles([STAFF_ROLE]) or jwt.validate_roles([PPR_STAFF_ROLE]):
        return True
    return False


def is_document_authorized(jwt: JwtManager) -> bool:
    """Return True if the user token can submit document requests: staff or service account only."""
    if not jwt:
        return False
    if jwt.validate_roles([STAFF_ROLE]) or jwt.validate_roles([PPR_STAFF_ROLE]) or jwt.validate_roles([SYSTEM_ROLE]):
        return True
    return False


def is_report_authorized(jwt: JwtManager) -> bool:
    """Return True if the user can submit application report requests: staff or service account."""
    if not jwt:
        return False
    if jwt.validate_roles([STAFF_ROLE]) or jwt.validate_roles([PPR_STAFF_ROLE]) or jwt.validate_roles([SYSTEM_ROLE]):
        return True
    return False


def is_scanner_authorized(jwt: JwtManager) -> bool:
    """Return True if the user can submit desktop scanner application requests: staff or service account only."""
    if not jwt:
        return False
    if jwt.validate_roles([STAFF_ROLE]) or jwt.validate_roles([PPR_STAFF_ROLE]) or jwt.validate_roles([SYSTEM_ROLE]):
        return True
    return False


def is_convert_authorized(jwt: JwtManager) -> bool:
    """Return True if the user can submit pdf convert requests: staff or service account only."""
    if not jwt:
        return False
    if jwt.validate_roles([STAFF_ROLE]) or jwt.validate_roles([PPR_STAFF_ROLE]) or jwt.validate_roles([SYSTEM_ROLE]):
        return True
    return False


def is_search_authorized(jwt: JwtManager) -> bool:
    """Return True if the user can submit document search requests: staff or service account."""
    if not jwt:
        return False
    if jwt.validate_roles([STAFF_ROLE]) or jwt.validate_roles([PPR_STAFF_ROLE]) or jwt.validate_roles([SYSTEM_ROLE]):
        return True
    return False
