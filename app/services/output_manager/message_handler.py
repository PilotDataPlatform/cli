# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import io

import qrcode

import app.services.logger_services.log_functions as logger
from app.models.service_meta_class import MetaService


class SrvOutPutHandler(metaclass=MetaService):
    @staticmethod
    def login_device_code_qrcode(url: str):
        """Print QRCode with login url!"""
        qr = qrcode.QRCode(version=1, border=1)
        qr.add_data(url)
        f = io.StringIO()
        qr.print_ascii(out=f)
        f.seek(0)
        return logger.info(f.read())

    @staticmethod
    def login_input_device_code(url: str):
        """Access the url and input the device code!"""
        return logger.succeed(f'Please, access {url} to proceed')

    @staticmethod
    def login_input_device_error():
        """Error to get device code!"""
        return logger.error('Error to get device code!')

    @staticmethod
    def validation_login_input_device_error():
        """Error to validate the device code login!"""
        return logger.error('Error to validate the device code login, please try again!')

    @staticmethod
    def check_login_device_validation():
        """Waiting validation finish."""
        return logger.info('Waiting validation finish...')

    @staticmethod
    def login_success():
        """Login succeed!"""
        return logger.succeed('Welcome to the Command Line Tool!')

    @staticmethod
    def abort_if_false(ctx, param, value):
        """e.g. Logout cancelled!"""
        if not value:
            logger.warning('Logout cancelled.')
            ctx.exit()

    @staticmethod
    def logout_success():
        """e.g. Logout succeed!"""
        return logger.succeed('Logged out successfully. Bye!')

    @staticmethod
    def list_success(category):
        """Fetch list succeed!"""
        return logger.succeed(f'{category} list fetched successfully!')

    @staticmethod
    def start_zipping_file():
        """e.g. Start ziping files."""
        return logger.info('Started zipping files.')

    @staticmethod
    def attach_manifest():
        """e.g. Attribute attached."""
        return logger.info('Attribute attached')

    @staticmethod
    def all_file_uploaded():
        """e.g. All files uploaded.

        Job Done.
        """
        return logger.succeed('All uploading jobs have finished.')

    @staticmethod
    def all_manifest_fetched():
        """e.g. All attributes fetched."""
        return logger.succeed('All Attributes fetched successfully.')

    @staticmethod
    def project_has_no_manifest(project_code):
        """e.g. Project 0212 does not have any attribute yet."""
        return logger.warning(
            f'No attributes exist in Project {project_code} yet, or you may need to check your project list'
        )

    @staticmethod
    def export_manifest_template(name):
        """e.g. Succeed, template saved: 0212_Manifest1_template.json."""
        return logger.succeed('Template saved successfully: {}'.format(name))

    @staticmethod
    def export_manifest_definition(name):
        """e.g. Succeed, definition saved: 0212_Manifest1_definition.json."""
        return logger.succeed('Attribute definition saved successfully: {}'.format(name))

    @staticmethod
    def file_manifest_validation(post_result):
        """e.g. File attribute validated: True."""
        return logger.info(f'File attribute validation passed: {post_result == "valid"}')

    @staticmethod
    def uploading_files(uploader, project_code, resumable_total_size, resumable_total_chunks, resumable_relative_path):
        return logger.info(
            'uploader: {}\n',
            uploader,
            'project_code: {}\n',
            project_code,
            'total_size: {}\n',
            resumable_total_size,
            'total_chunks: {}\n',
            resumable_total_chunks,
            'resumable_relative_path {}\n',
            resumable_relative_path,
        )

    @staticmethod
    def preupload_success():
        """e.g. pre-upload succeed."""
        return logger.info('Pre-upload complete.')

    @staticmethod
    def resume_check_success():
        """e.g. notify the resumable check succeed."""
        return logger.info('Resumable upload check complete.')

    @staticmethod
    def resume_warning(num_of_files: int):
        """e.g. notify the user if they comfirm the resumable upload."""
        return logger.warning(f'Resume the upload for {num_of_files} files.')

    @staticmethod
    def start_finalizing():
        """e.g. Start finalizing."""
        return logger.info('Starting finalization...')

    @staticmethod
    def finalize_upload():
        """e.g. upload job is finalizing, please wait..."""
        return logger.info('Upload job is finalizing, please wait...')

    @staticmethod
    def upload_job_done():
        """e.g. upload job done..."""
        return logger.info('Upload job complete.')

    @staticmethod
    def start_uploading(filename):
        """e.g. Start Uploading: ./test_file."""
        logger.info(f'Starting upload of: {filename}')

    @staticmethod
    def start_requests():
        """e.g. start requests."""
        logger.info('Starting request...')

    @staticmethod
    def print_list_header(col1, col2):
        """e.g. NAME                              CODE."""
        logger.info(col1.center(40, ' ') + col2.center(40, ' '))  # noqa: G003
        logger.info('-' * 75)

    @staticmethod
    def print_list_parallel(item_name, item_code):
        logger.info(str(item_name).center(40, ' ') + ' |' + str(item_code).center(37, ' '))  # noqa: G003

    @staticmethod
    def count_item(current_page, category, project_api_response_dict):
        """e.g. NUMBER OF PROJECTS 21."""
        logger.info(f'\nPage: {current_page}, Number of {category}: {len(project_api_response_dict)}')

    @staticmethod
    def download_success(file_name):
        logger.succeed(f'File has been downloaded successfully and saved to: {file_name}')

    @staticmethod
    def dataset_current_version(version):
        logger.succeed(f'Current dataset version: {version}')

    @staticmethod
    def download_status(status):
        logger.info(f'Preparing status: {status}')

    @staticmethod
    def print_manifest_table(manifest_list):
        """
        Manifest1
        --------------------------------------------------------------------------
        |    Attribute Name    |       Type      |       Value        | Optional |
        --------------------------------------------------------------------------
        |        attr1         | multiple_choice |       a1,a2        |  False   |
        --------------------------------------------------------------------------
        |        attr2         |       text      |        None        |   True   |
        --------------------------------------------------------------------------
        """
        col_width = 76
        optional_width = 10
        type_width = 17
        attribute_name_width = 22
        value_width = 22
        if not isinstance(manifest_list, list):
            manifest_list = [manifest_list]
        for m in manifest_list:
            manifest_name = str(m.get('name'))
            logger.info('\n' + manifest_name)  # noqa: G003
            logger.info('-'.ljust(col_width, '-'))
            logger.info(  # noqa: G003
                '|'  # noqa: G003
                + 'Attribute Name'.center(attribute_name_width, ' ')  # noqa: G003
                + '|'  # noqa: G003
                + 'Type'.center(type_width, ' ')  # noqa: G003
                + '|'  # noqa: G003
                + 'Value'.center(value_width, ' ')  # noqa: G003
                + '|'  # noqa: G003
                + 'Optional'.center(optional_width, ' ')  # noqa: G003
                + '|'  # noqa: G003
            )
            attributes = m.get('attributes')
            if not attributes:
                attributes = [{'name': '', 'optional': '', 'type': '', 'value': ''}]
            for attr in attributes:
                if isinstance(attr.get('options', ''), list):
                    options = ' '.join(attr.get('options', ''))
                else:
                    options = str(attr.get('options', ''))
                attr_name = str(attr['name'])[0:17] + '...' if len(str(attr['name'])) > 17 else str(attr['name'])
                attr_option = str(attr['optional'])
                attr_type = str(attr['type'])
                attr_value = options[0:17] + '...' if len(options) > 17 else options
                logger.info('-'.ljust(col_width, '-'))
                logger.info(
                    '|'  # noqa: G003
                    + attr_name.center(attribute_name_width, ' ')  # noqa: G003
                    + '|'  # noqa: G003
                    + attr_type.center(type_width, ' ')  # noqa: G003
                    + '|'  # noqa: G003
                    + attr_value.center(value_width, ' ')  # noqa: G003
                    + '|'  # noqa: G003
                    + attr_option.center(optional_width, ' ')  # noqa: G003
                    + '|'  # noqa: G003
                )
            logger.info('-'.ljust(col_width, '-'))

    @staticmethod
    def print_container_registry_project_list(project_names):
        logger.succeed('Retrieved all available projects')
        logger.info(project_names)

    @staticmethod
    def print_container_registry_repo_list(repo_names, project):
        if project:
            logger.succeed(f'Retrieved all available repositories in {project}')
        else:
            logger.succeed('Retrieved all available repositories')
        logger.info(repo_names)

    @staticmethod
    def container_registry_create_project_success(project_name):
        logger.succeed(f'Created new project {project_name}')

    @staticmethod
    def container_registry_get_secret_success(secret):
        logger.succeed(f'Retrieved user secret: {secret}')

    @staticmethod
    def container_registry_share_project_success(role, project, username):
        logger.succeed(f'Shared project {project} with {username} as {role}')
