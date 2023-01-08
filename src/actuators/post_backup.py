import os
import re
import subprocess
from abc import ABC
from datetime import datetime
from pathlib import Path

from jsonschema.validators import validate

from src.actuators.actuators import PythonActuator, ActuatorMetadata
from src.actuators.exceptions import RunningException


class AbstractPostBackup(PythonActuator, ABC):

    def _actuator_type(self) -> str:
        return 'post-backup'


class CleanFolderPostBackup(AbstractPostBackup):
    validation_schema = {'type': 'object', 'properties': {
        'retention': {
            'type': 'integer',
            'minimum': 1,
            'description': 'Retention duration in days'}},
                         'required': ['retention'],
                         'additionalProperties': False}
    fileRegex = re.compile(r'^(\d+-\d+-\d+T\d+:\d+:\d+)')

    def __init__(self, global_context: dict, args: dict, metadata: dict[str, dict[str, ActuatorMetadata]] = None):
        super().__init__(global_context, args, metadata)
        self.retention = None
        self._output_directory = None

    @staticmethod
    def module_name() -> str:
        return 'cleanFolder'

    def _get_params(self) -> None:
        validate(self._args, self.validation_schema)

        self.retention = self._args['retention']

    @staticmethod
    def _file_prefix() -> str:
        return datetime.today().isoformat(timespec='seconds') + '-'

    def _prepare_run_backup(self) -> dict:
        # Validate metadata
        output_directories = [v.get('output-directory') for (i, v) in self._metadata['writer'].items()]
        if len(output_directories) != 1:  # Because we need at least one, and it can not be greater than 1
            raise ValueError('output-directory must be defined in writer module')
        self._output_directory = Path(output_directories[0])

        file_preservation_window = max(
            [v.get('file-preservation-window') for (i, v) in self._metadata['reader'].items()])
        if self.retention < file_preservation_window:
            print(
                '\033[93m' + f'WARNING: retention [{self.retention}] is lower than the minimum possible '
                             f'[{file_preservation_window}]. Retention value is override by the minimum')
            self.retention = file_preservation_window

        files_to_remove = []
        today = datetime.today()
        with os.scandir(self._output_directory) as it:
            entry: os.DirEntry
            for entry in it:
                matches = self.fileRegex.search(entry.name)
                if matches is None or len(matches.groups()) != 1:
                    continue
                creation_date = datetime.fromisoformat(matches.group(1))
                diff_days = (today - creation_date).days
                if diff_days > self.retention:
                    files_to_remove.append(entry.path)
        return {'files-to-remove': files_to_remove}

    def _run_backup(self, args: dict) -> None:
        for file_path in args['files-to-remove']:
            try:
                os.remove(file_path)
            except OSError as e:
                raise RunningException(f'Unable to remove file [{file_path}].\nReason: {e}') from e

    def _dry_run_backup(self, args: dict) -> None:
        for file_path in args['files-to-remove']:
            print(f'File [{file_path}] would have been deleted.')


class RsyncPostBackup(AbstractPostBackup):
    validation_schema = {'type': 'object', 'properties': {
        'ip-addr': {
            'type': 'string',
            'description': 'Ip address of remote host'},
        'dest-module': {
            'type': 'string',
            'description': 'Destination rsyncd module'},
        'dest-folder': {
            'type': 'string',
            'description': 'Destination folder'},
        'user': {
            'type': 'string',
            'description': 'Username to use to log in'},
        'password-file': {
            'type': 'string',
            'description': 'Path to the file that contains the password'}},
                         'required': ['ip-addr', 'dest-folder', 'user'],
                         'additionalProperties': False}

    def __init__(self, global_context: dict, args: dict, metadata: dict[str, dict[str, ActuatorMetadata]] = None):
        super().__init__(global_context, args, metadata)
        self._output_directory = None

    @staticmethod
    def module_name() -> str:
        return 'rsync'

    def _get_params(self) -> None:
        validate(self._args, self.validation_schema)

        self.ip_addr = self._args['ip-addr']
        self.dest_module = self._args.get('dest-module')
        self.dest_folder = self._args['dest-folder']
        self.user = self._args['user']
        self.password_file = self._args.get('password-file')
        if self.password_file is not None:
            password_file = Path(self._args['password-file'])
            if not password_file.is_file():
                raise Exception('password-file [' + self._args['password-file'] + '] doesn\'t exists')
            if not os.access(password_file, os.R_OK):
                raise Exception('password-file [' + self._args['password-file'] + '] is not readable')
            if os.stat(password_file).st_mode & 0o77 != 0o0:
                raise Exception(
                    'password-file [' + self._args['password-file'] + '] must not be readable from group and '
                                                                      'from others')

    def _prepare_run_backup(self) -> dict:
        # Validate metadata
        output_directories = [v.get('output-directory') for (i, v) in self._metadata['writer'].items()]
        if len(output_directories) != 1:  # Because we need at least one, and it can not be greater than 1
            raise ValueError('output-directory must be defined in writer module')
        self._output_directory = output_directories[0]

        cmd = 'rsync --no-inc-recursive --exclude={"lost+found/"} --delete-after'.split(' ')
        if self.password_file is not None:
            cmd.extend(['--password-file', self.password_file])
        cmd.append(self._output_directory)
        destination = self.user + '@' + self.ip_addr
        if self.dest_module is not None:
            destination += '::' + self.dest_module + '/'
        else:
            destination += ':/'
        if self.dest_folder[0] == '/':  # Remove first slash if exists
            destination += self.dest_folder[1:]
        else:
            destination += self.dest_folder
        cmd.append(destination)

        return {'cmd': cmd}

    def _run_backup(self, args: dict) -> None:
        with subprocess.run(args['cmd'], capture_output=True, shell=False, text=True) as process:
            if process.returncode != 0:
                raise RunningException('Error during execution of rsync\n'
                                       f'Rsync output: {process.stderr}')

    def _dry_run_backup(self, args: dict) -> None:
        print(f'''Command [{' '.join(args['cmd'])}] would have been ran.''')
