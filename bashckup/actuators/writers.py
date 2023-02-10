import logging
import os
import re
import subprocess
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import IO, AnyStr, Any

from jsonschema.validators import validate

from bashckup.actuators.actuators import CommandActuator
from bashckup.actuators.exceptions import ParameterException

datetimeOutputFileRegex = re.compile(r'^(\d+-\d+-\d+T\d+:\d+:\d+)')
outputFileRegex = re.compile(r'^(\d+-\d+-\d+T\d+:\d+:\d+)-(.*)')


class AbstractWriter(CommandActuator, ABC):

    def _actuator_type(self) -> str:
        return 'writer'

    def generate_backup_process(self, stdin: IO[AnyStr], stdout: IO[AnyStr] = subprocess.DEVNULL) \
            -> subprocess.Popen:
        return super().generate_backup_process(stdin, stdout)

    def generate_restore_process(self, stdin: IO[AnyStr] = None, stdout: IO[AnyStr] = subprocess.PIPE) \
            -> subprocess.Popen:
        return super().generate_backup_process(stdin, stdout)


class FileWriter(AbstractWriter):
    validation_schema = {'type': 'object',
                         'properties': {
                             'path': {
                                 'type': 'string',
                                 'description': 'Path to the output folder'},
                             'file-name': {
                                 'type': 'string',
                                 'description': 'File name of the backup file'}
                         },
                         'required': ['path', 'file-name'],
                         'additionalProperties': False}

    @staticmethod
    def module_name() -> str:
        return 'outputFile'

    def _get_params(self) -> None:
        validate(self._args, self.validation_schema)

        self.path = Path(self._args['path'])
        self.file_name = self._args['file-name']
        self._output_folder = self.path

        # If folder doesn't exist, it will be created by _pre_run_tasks
        if self._output_folder.exists() and not self._output_folder.is_dir():
            raise ParameterException(f'''Directory [{self._output_folder}] is NOT a directory''', 'path',
                                     self._backup_id, self.module_name())
        if self._output_folder.exists() and not os.access(self._output_folder, os.W_OK):
            raise ParameterException(f'''Directory [{self._output_folder}] is not writable''', 'path',
                                     self._backup_id, self.module_name())

    def _generate_backup_cmd(self) -> [str]:
        cmd = ['cat']
        return cmd

    # Override because this module have a special way to managed process
    def generate_dry_run_backup_cmd(self) -> [str]:
        return ['>', str(self._output_file_path)]

    # Override because this module have a special way to managed process
    def generate_backup_process(self, stdin: IO[AnyStr], stdout: IO[AnyStr] = None) -> subprocess.Popen:
        with open(self._output_file_path, 'w') as f:
            return super().generate_backup_process(stdin, f)

    def _pre_run_tasks(self) -> None:
        #  Create backup folder
        if self._dry_run is False:
            logging.info('Folder [%s] created', str(self._output_folder))
            os.makedirs(self._output_folder, exist_ok=True, mode=0o750)
        else:
            logging.info('Folder [%s] would have been created.', self._output_folder)
        if self._isBackup:
            self._backup_datetime = datetime.today()
            self._file_prefix = self._backup_datetime.isoformat(timespec='seconds') + '-'
            self._output_file_path = self._output_folder / (self._file_prefix + self.file_name)
        else:
            latest_backup = self._get_latest_backup_file()
            self._backup_datetime = latest_backup['backup-datetime']
            self._file_prefix = self._backup_datetime.isoformat(timespec='seconds') + '-'
            self._output_file_path = latest_backup['file-path']

    def _generate_metadata(self) -> dict:
        return {'output-directory': str(self._output_folder), 'file-prefix': self._file_prefix,
                'backup-datetime': self._backup_datetime.isoformat(timespec='seconds')}

    def _get_latest_backup_file(self) -> {Any}:
        latest_backup_path = None
        latest_backup_datetime = None
        with os.scandir(self._output_folder) as it:
            entry: os.DirEntry
            for entry in it:
                matches = outputFileRegex.search(entry.name)
                if matches is None or len(matches.groups()) != 2:
                    continue
                if matches.group(2) != self.file_name:
                    continue
                current_backup_datetime = datetime.fromisoformat(matches.group(1))
                if latest_backup_datetime is None or latest_backup_datetime < current_backup_datetime:
                    latest_backup_datetime = current_backup_datetime
                    latest_backup_path = entry.path
        if latest_backup_path is None:
            raise ParameterException(f'''path [{str(self._output_folder)}] does not contains any backup''',
                                     'path', self._backup_id, self.module_name())

        return {'file-path': latest_backup_path, 'backup-datetime': latest_backup_datetime}

    def _generate_restore_cmd(self) -> [str]:
        cmd = ['cat', self._output_file_path]

        return cmd
