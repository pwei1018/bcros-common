# Application Name

BC Registries Notify API

## Background


## Technology Stack Used
* Python, Flask
* Postgres -  SQLAlchemy, pg8000 & alembic

## Third-Party Products/Libraries used and the the License they are covert by

## Project Status

## Documnentation

GitHub Pages (https://guides.github.com/features/pages/) are a neat way to document you application/project.

## Security

## Files in this repository

## Environment Variables
Copy '.env.sample' to '.env' and replace the values

### Development Setup
Run `poetry shell`
Run `poetry install`

### Bump version
Run `poetry version (patch, minor, major, prepatch, preminor, premajor, prerelease)`

### Running the db migration - add new version/upgrade/downgrade
export DEPLOYMENT_ENV=migration
Run `poetry run flask db revision -m "xxx"`
Run `poetry run flask db upgrade`
Run `poetry run flask db downgrade`

### Running the Notify-API locally
Run `poetry run flask run`

### Running Linting
Run `poetry run ruff check`

### Running Unit Tests
- For all tests run `poetry run pytest -v -s`
- For an individual file run `poetry run pytest -v -s ./tests/unit/api/filename.py`
- For an individual test case run `poetry run pytest -v -s ./tests/unit/api/filename.py::test-case-name`

## Deployment

See https://github.com/bcgov/bcregistry-sre/blob/main/.github/workflows/notify-api-cd-gcp.yaml
See https://github.com/bcgov/bcregistry-sre/blob/main/.github/workflows/notify-api-cd-ocp.yaml

## Getting Help or Reporting an Issue

To report bugs/issues/feature requests, please file an [issue](../../issues).

## How to Contribute

If you would like to contribute, please see our [CONTRIBUTING](./CONTRIBUTING.md) guidelines.

Please note that this project is released with a [Contributor Code of Conduct](./CODE_OF_CONDUCT.md).
By participating in this project you agree to abide by its terms.

## License

    Copyright 2025 Province of British Columbia

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.