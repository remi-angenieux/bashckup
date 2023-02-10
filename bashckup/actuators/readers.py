import os
import subprocess
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import IO, AnyStr, Dict

from jsonschema.validators import validate

from bashckup.actuators import writers
from bashckup.actuators.actuators import ActuatorMetadata, CommandActuator
from bashckup.actuators.exceptions import ParameterException


class AbstractReader(CommandActuator, ABC):

    def _actuator_type(self) -> str:
        return 'reader'

    def generate_backup_process(self, stdin: IO[AnyStr] = None, stdout: IO[AnyStr] = subprocess.PIPE) \
            -> subprocess.Popen:
        return super().generate_backup_process(stdin, stdout)


class FileReader(AbstractReader):
    defaultLevel0frequency = 'weekly'
    validation_schema = {'type': 'object',
                         'properties': {
                             'path': {
                                 'type': 'string',
                                 'description': 'Folder path for the backup. It will create a sub-folder with the '
                                                'backup id'},
                             'incremental-metadata-file-prefix': {
                                 'type': 'string',
                                 'description': 'Name of metadata-file used to store difference between backups'},
                             'level-0-frequency': {
                                 'type': 'string',
                                 'enum': ['weekly', 'monthly'],
                                 'default': defaultLevel0frequency,
                                 'description': 'When a full backup have to be done ? You have to choose in ['
                                                '\'weekly\', \'monthly\']'}
                         },
                         'required': ['path'],
                         'additionalProperties': False}

    def __init__(self, global_context: dict, args: dict, metadata: Dict[str, Dict[str, ActuatorMetadata]] = None):
        super().__init__(global_context, args, metadata)
        self._file_prefix = None
        self._output_directory = None

    @staticmethod
    def module_name() -> str:
        return 'files'

    def _get_params(self) -> None:
        validate(self._args, self.validation_schema)
        if self._args.get('level-0-frequency') is not None and self._args.get(
                'incremental-metadata-file-prefix') is None:
            raise ParameterException('level-0-frequency can be used only with incremental-metadata-file-prefix',
                                     'level-0-frequency', self._backup_id, self.module_name())

        self.incrementalMetadataFilePrefix = self._args.get('incremental-metadata-file-prefix')
        self.path = self._args['path']
        self.level0Frequency = self._args.get('level-0-frequency', self.defaultLevel0frequency)

    def _generate_backup_cmd(self) -> [str]:
        # Validate metadata
        self._validate_register_metadata()

        cmd = ['tar']
        if self._verbose:
            cmd.append('--verbose')
        if self.incrementalMetadataFilePrefix is not None:
            cmd.extend(['--listed-incremental', str(self._generate_incremental_metadata_file_name())])
        cmd.extend(['--create', self.path])
        return cmd

    def _validate_register_metadata(self):
        """
        Validates metadata and register attributes with it
        """
        output_directories = [v.get('output-directory') for (i, v) in self._metadata['writer'].items()]
        if len(output_directories) != 1:  # Because we need at least one, and it can not be greater than 1
            raise ValueError('output-directory must be defined in writer module')
        self._output_directory = output_directories[0]
        file_prefixes = [v.get('file-prefix') for (i, v) in self._metadata['writer'].items()]
        if len(file_prefixes) != 1:  # Because we need at least one, and it can not be greater than 1
            raise ValueError('file-prefix must be defined in writer module')
        self._file_prefix = file_prefixes[0]
        backups_datetime = [v.get('backup-datetime') for (i, v) in self._metadata['writer'].items()]
        if len(backups_datetime) != 1:  # Because we need at least one, and it can not be greater than 1
            raise ValueError('backup-datetime must be defined in writer module')
        self._backup_datetime = datetime.fromisoformat(backups_datetime[0])

    def _generate_incremental_metadata_file_name(self) -> Path:
        # self._file_prefix
        file_name = self.incrementalMetadataFilePrefix
        if self.level0Frequency == 'weekly':
            file_name += '-w' + self._backup_datetime.strftime('%V')
        elif self.level0Frequency == 'monthly':
            file_name += '-m' + self._backup_datetime.strftime('%m')
        else:
            raise ValueError(f'Frequency {self.level0Frequency} is not managed')
        file_name += '.snar'

        # Search if an incremental file already exists
        incremental_file_exists = False
        with os.scandir(self._output_directory) as it:
            entry: os.DirEntry
            for entry in it:
                if entry.name.endswith(file_name):
                    file_name = entry.name
                    incremental_file_exists = True
                    break
        # If incremental file does not exist then create a file with the prefix
        if not incremental_file_exists:
            file_name = self._file_prefix + file_name
        return Path(self._output_directory) / file_name

    def _generate_metadata(self) -> dict:
        days = 0
        # Incremental backup, so we need to keep level0 backup
        if self._isBackup and self.incrementalMetadataFilePrefix is not None:
            if self.level0Frequency == 'weekly':
                # We can use datetime.today() instead of datetime set by writer because we add 1 day of margin
                # And in this part of code we can not have datetime set by writer
                week_number = datetime.today().strftime('%Y/%W')
                window_first_day = datetime.strptime(week_number + '/1', '%Y/%W/%w')  # Year/week-number/day-of-week
                days = (datetime.today() - window_first_day).days + 1
                # +1 because we want to protect all the day, not actual time of the first day of the week
            elif self.level0Frequency == 'monthly':
                month_number = datetime.today().strftime('%Y/%m/01')
                window_first_day = datetime.strptime(month_number, '%Y/%m/%d')  # Year/month/day-of-month
                days = (datetime.today() - window_first_day).days + 1
                # +1 because we want to protect all the day, not actual time of the first day of the month
            else:
                raise ValueError(f'Frequency {self.level0Frequency} is not managed')
        return {'file-preservation-window': days}

    def _generate_restore_cmd(self) -> [str]:
        # Validate metadata
        self._validate_register_metadata()
        cmd = ['tar']
        if self._verbose:
            cmd.append('--verbose')
        if self.incrementalMetadataFilePrefix is not None:
            cmd.extend(['--listed-incremental', str(self._generate_incremental_metadata_file_name())])
        cmd.extend(['--extract', self.path])

        return cmd

    # Override because we need to back up files before the restoration
    def generate_restore_process(self, stdin: IO[AnyStr] = None,
                                 stdout: IO[AnyStr] = subprocess.PIPE) -> subprocess.Popen:
        # Back up src files before restoration
        src_path = Path(self.path)
        backup_path = src_path.parents[0] / (src_path.name + '-bck')
        os.rename(src_path, backup_path)
        return super().generate_backup_process(stdin, stdout)


class MariaDBReader(AbstractReader):
    validation_schema = {'type': 'object',
                         'properties': {
                             'database-name': {
                                 'type': 'string',
                                 'description': 'Name of mariadb database'}
                         },
                         'required': ['database-name'],
                         'additionalProperties': False}

    @staticmethod
    def module_name() -> str:
        return 'mariaDBDatabase'

    def _get_params(self) -> None:
        validate(self._args, self.validation_schema)

        self.databaseName = self._args['database-name']

    def _generate_backup_cmd(self) -> [str]:
        cmd = ['mysqldump']
        if self._verbose:
            cmd.append('--verbose')
        cmd.append(self.databaseName)
        return cmd

    def _generate_restore_cmd(self) -> [str]:
        cmd = ['mysql']
        if self._verbose:
            cmd.append('--verbose')
        cmd.append(self.databaseName)
        return cmd
