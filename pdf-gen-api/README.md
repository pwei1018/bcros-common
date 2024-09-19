# Application Name
BC Registries PDF Form Auto Generation

## Description
Generate latest version of filing PDF forms based on latest Business Schemas.

## Technology Stack Used
- Python 3.12, ReportLab, Flask(planned, not yet implemented)

## Project Status
As of 2024-09-19 in **Development**

## Development Environment
Follow the instructions of the [Development Readme](https://github.com/bcgov/entity/blob/master/docs/development.md)
to setup your local development environment.
- Make sure you have Python 3.12 installed. You can check `python3.12 --version` 
- Make sure you have pyenv 3.12 installed. You can check `pyenv versions`

## Development Setup
1. Follow the [instructions](https://github.com/bcgov/entity/blob/master/docs/setup-forking-workflow.md) to checkout the project from GitHub.
2. **Open the pdf-gen-api directory in VS Code to treat it as a project (or WSL project).** To prevent version clashes, set up a
virtual environment to install the Python packages used by this project.
3. Run `make setup` to set up the virtual environment and install libraries.

## Run PDF-GEN-API
Currently, only able to run locally as a local application, tht API is not yet built. And not yet deployed.
1. Run the service `make run`
2. Select a form to generate from the terminal UI provided
3. OpenAPI Docs will be added later when API is built.

## Run Linting
Run `make lint`

## Run Unit Tests
Run `make test`
<br>Coverage is not yet implemented.


