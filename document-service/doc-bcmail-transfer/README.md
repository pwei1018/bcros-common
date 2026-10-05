[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

# Application Name

BC Registries Document Records Service (DRS) BCMail+ scanned documents synchronization. 

## Technology Stack Used
* Python
* Postgres -  psycopg2-binary
* GCP Cloud Storage

## Project Status

## Documentation
### Summary:
Synchronize legacy documents recently scanned by BCMail+ with the DRS. If documents have been copied to
the BCRS LAN network drive (initial migration), access requires running a BCGOV VPN and mounting the drive
locally. With this configuration, where the MIGRATE_LAN env var is true, the job can only run locally.

For connectivity testing the env var LIST_FILES can be set to true. With this setting the job simply lists the
BCMail+ remote sub-directories containing files to be migrated. No documents are migrated.

### Detail:
Based on the MIGRATE_LAN and LIST_FILES environmet variables determine which task to perform:
1. List LAN sub-directories: MIGRATE_LAN=true, LIST_FILES=true:
    a. Print to the console all sub-directories an files in the BCMAIL_LAN_DIR directory.
2. Migrate LAN sub-directory files: requires BCMAIL_LAN_DIR, BCMAIL_LAN_FOLDERS, and BCMAIL_TEMP_DIR:
   MIGRATE_LAN=true, LIST_FILES=false:
    Iterate through the LAN sub-directories identified by BCMAIL_LAN_FOLDERS:
    a. Copy each file to a local temporary directory.
    b. Upload the temporary file contents to a dedicated BCMail GCP cloud storage bucket, then delete the
       temporary file.
    After all files have been stored in GCP CS:
    a. Update the file summary information with DRS document record information.
    b. Generate a CSV formatted summary of the job migration, 1 row per document migrated, and store it in
       GCP CS.
    c. Send an email notification of the job with a link to the CSV file.
3. List Remote SFTP sub-directories: MIGRATE_LAN=false, LIST_FILES=true:
    a. Open a SFTP session with the BCMail+ service.
    b. Print to the console all sub-directories an files in the SFTP_DIR directory.
4. Migrate SFTP directory files: requires SFTP_* environment variables:
   MIGRATE_LAN=false, LIST_FILES=false:
    Iterate through the SFTP_DIR sub-directories. Files in SFTP_DIR are ignored:
    a. Read each remote file and load as in memory bytes.
    b. Upload the remote file contents to a dedicated BCMail GCP cloud storage bucket.
    After all files have been stored in GCP CS:
    a. Update the file summary information with DRS document record information.
    b. Generate a CSV formatted summary of the job migration, 1 row per document migrated, and store it in
       GCP CS.
    c. Send an email notification of the job with a link to the CSV file.

## Security

## Environment Variables
Copy 'env_sample' to '.env' and replace the values

### Development Setup
Run `poetry install`

Run `poetry shell`

### Running the job (may require running VPN)
Run `python -m doc_bcmail_transfer`

### Running Linting
Run `poetry run isort . --check`
Run `poetry run black . --check`
Run `poetry run pylint src`
Run `poetry run flake8 src`

## Getting Help or Reporting an Issue

To report bugs/issues/feature requests, please file an [issue](../../issues).

## How to Contribute

If you would like to contribute, please see our [CONTRIBUTING](./CONTRIBUTING.md) guidelines.

Please note that this project is released with a [Contributor Code of Conduct](./CODE_OF_CONDUCT.md).
By participating in this project you agree to abide by its terms.

## License

    Copyright 2026 Province of British Columbia

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

