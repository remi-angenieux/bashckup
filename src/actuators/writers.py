import os
import subprocess
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import IO, AnyStr

from jsonschema.validators import validate

from src.actuators.actuators import CommandActuator
from src.actuators.exceptions import ParameterException


class AbstractWriter(CommandActuator, ABC):

    def _actuator_type(self) -> str:
        return 'writer'

    def generate_backup_process(self, stdin: IO[AnyStr], stdout: IO[AnyStr] = subprocess.DEVNULL) \
            -> subprocess.Popen[str]:
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

        path = Path(self._args['path'])
        if not path.exists():
            raise ParameterException(f'''Path {self._args['path']} does not exists, please create it''', 'path',
                                     self._backup_id, self.module_name())
        self.path = path
        self.file_name = self._args['file-name']
        self._output_folder = self.path / self._backup_id

        # If folder doesn't exist, it will be created by _pre_run_tasks
        if self._output_folder.exists() and not self._output_folder.is_dir():
            raise ParameterException(f'''Directory [{self._output_folder}] is NOT a directory''', 'path',
                                     self._backup_id, self.module_name())
        if self._output_folder.exists() and not os.access(self._output_folder, os.W_OK):
            raise ParameterException(f'''Directory [{self._output_folder}] is not writable''', 'path',
                                     self._backup_id, self.module_name())
        self._output_file_path = self._output_folder / (self._file_prefix() + self.file_name)

    @staticmethod
    def _file_prefix() -> str:
        return datetime.today().isoformat(timespec='seconds') + '-'

    def _generate_backup_cmd(self) -> [str]:
        cmd = ['cat']
        return cmd

    """
    Override because this module have a special way to managed process
    """

    def generate_dry_run_backup_cmd(self) -> [str]:
        return ['>', str(self._output_file_path)]

    """
    Override because this module have a special way to managed process
    """

    def generate_backup_process(self, stdin: IO[AnyStr], stdout: IO[AnyStr] = None) -> subprocess.Popen[str]:
        with open(self._output_file_path, 'w') as f:
            return super().generate_backup_process(stdin, f)

    def _pre_run_tasks(self) -> None:
        #  Create backup folder
        if self._dry_run is False:
            os.makedirs(self._output_folder, exist_ok=True, mode=0o750)
        else:
            print(f'Folder [{self._output_folder}] would have been created.')

    def _generate_metadata(self) -> dict:
        return {'output-directory': str(self._output_folder), 'file-prefix': self._file_prefix()}
