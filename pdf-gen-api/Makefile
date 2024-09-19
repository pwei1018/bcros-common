
# Define variables
CURRENT_DIR := $(shell pwd)
VENV_DIR := $(CURRENT_DIR)/venv
PROJECT_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME :=pdf_gen_api


# Detect current platform (Linux / Mac)
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S), Linux)
    PYTHON := $(VENV_DIR)/bin/python
    PIP := $(VENV_DIR)/bin/pip
else
    PYTHON := $(VENV_DIR)/bin/python3
    PIP := $(VENV_DIR)/bin/pip3
endif


##################################
# Run the App                    #
##################################
run:
	. venv/bin/activate && cd src && $(PYTHON) -m pdf_gen_api.main

# Setup & Clean
clean: 
	rm -rf $(VENV_DIR) __pycache__ *.pyc *.pyo *.pyd .pytest_cache

# Install Python virtual environment
venv:
	python3.12 -m venv $(VENV_DIR)

##################################
# Initial setup                  #
##################################
setup: clean install update-schemas

# re-install packages
install: venv
	$(shell mkdir -p demo_output)
	$(shell . venv/bin/activate)
	$(PIP) install --upgrade pip 
	$(PIP) install -r requirements.txt 
	$(PIP) install -e . 

# Download / update Business Schemas JSON files
update-schemas: 
	@echo "Updating Business Schemas" &&\
	. venv/bin/activate && \
	cd $(PROJECT_ROOT) && \
	mkdir -p business_schemas && \
	cd business_schemas && \
	gitdir --flatten https://github.com/bcgov/business-schemas/tree/main/src/registry_schemas/schemas && \
	echo "Update Complete"


##################################
# Linting & Unit Tests           #
##################################
lint:
	. venv/bin/activate && pylint src/$(PROJECT_NAME)

test:
	. venv/bin/activate && pytest
