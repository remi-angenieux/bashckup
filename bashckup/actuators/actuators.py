import subprocess
from abc import abstractmethod
from typing import AnyStr, IO, Dict

from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from bashckup.actuators.exceptions import ParameterException


class ActuatorMetadata:
    _schema = {'type': 'object',
               'properties': {
                   'file-preservation-window': {
                       'type': 'integer',
                       'minimum': 0,
                       'description': 'How many days files have to stay, it override cleaner\'s specification.'},
                   'output-directory': {
                       'type': 'string',
                       'description': 'Path to backup folder'},
                   'file-prefix': {
                       'type': 'string',
                       'description': 'Prefix of each files (with timestamp)'},
                   'backup-datetime': {
                       'type': 'string',
                       'format': 'date-time',
                       'description': 'Date time of the backup'}
               },
               'additionalProperties': False
               }

    def __init__(self, metadata: dict):
        validate(metadata, self._schema)
        self.__dict__.update(metadata)

    def get(self, key):
        return self.__dict__.get(key)


class AbstractActuator:
    def __init__(self, global_context: dict, args: dict, metadata: Dict[str, Dict[str, ActuatorMetadata]] = None):
        self._backup_id = global_context['backup-id']
        self._dry_run = global_context['dry-run']
        self._verbose = global_context['verbose']
        self._isBackup = global_context['backup']
        self._isRestore = not global_context['backup']
        self._args: dict = args
        self._metadata: Dict[str, Dict[str, ActuatorMetadata]] = metadata

    @staticmethod
    @abstractmethod
    def module_name() -> str:
        pass

    @abstractmethod
    def _get_params(self) -> None:
        pass

    @abstractmethod
    def _actuator_type(self) -> str:
        pass

    def _pre_run_tasks(self) -> None:
        """ If an actuator needs to create something before running the backup plan, you can use this method """
        pass

    def _generate_metadata(self) -> dict:
        return {}

    def _validate_parameters(self) -> None:
        try:
            self._get_params()
        except ValidationError as e:
            raise ParameterException(f'{e.message}\n'
                                     f'''Helper: {e.schema.get('description')}''', e.json_path, self._backup_id,
                                     self.module_name()) from None

    def prepare_module(self):
        """ Do validation then run pre task and finally init metadata """
        self._validate_parameters()
        self._pre_run_tasks()
        return {self._actuator_type(): {self.module_name(): ActuatorMetadata(self._generate_metadata())}}


class CommandActuator(AbstractActuator):
    @abstractmethod
    def _generate_backup_cmd(self) -> [str]:
        pass

    def generate_dry_run_backup_cmd(self) -> [str]:
        if self._dry_run is False:
            raise Exception('You are not allowed to call this function outside dry-run')
        return self._generate_backup_cmd()

    def generate_backup_process(self, stdin: IO[AnyStr], stdout: IO[AnyStr]) -> subprocess.Popen:
        if self._dry_run is True:
            raise Exception('You are not allowed to call this function in dry-run')
        return subprocess.Popen(self._generate_backup_cmd(), shell=False, stdin=stdin, stdout=stdout,
                                stderr=subprocess.PIPE)

    @abstractmethod
    def _generate_restore_cmd(self) -> [str]:
        pass

    def generate_dry_run_restore_cmd(self) -> [str]:
        if self._dry_run is False:
            raise Exception('You are not allowed to call this function outside dry-run')
        return self._generate_restore_cmd()

    def generate_restore_process(self, stdin: IO[AnyStr],
                                 stdout: IO[AnyStr] = None) -> subprocess.Popen:
        if self._dry_run is True:
            raise Exception('You are not allowed to call this function in dry-run')
        return subprocess.Popen(self._generate_restore_cmd(), shell=False, stdin=stdin, stdout=stdout,
                                stderr=subprocess.PIPE)


class PythonActuator(AbstractActuator):
    @abstractmethod
    def _prepare_run_backup(self) -> dict:
        """
        Compute all data useful for running backup
        This data can be used to run the backup or write the verbose
        :return: Dict of computed elements
        """
        pass

    @abstractmethod
    def _run_backup(self, args: dict) -> None:
        pass

    @abstractmethod
    def _dry_run_backup(self, args: dict) -> None:
        pass

    def run_backup(self) -> None:
        args = self._prepare_run_backup()
        if self._dry_run is True:
            self._dry_run_backup(args)
        else:
            self._run_backup(args)

    @abstractmethod
    def _prepare_run_restore(self) -> dict:
        """
        Compute all data useful for running restoration
        This data can be used to run the restoration or write the verbose
        :return: Dict of computed elements
        """
        pass

    @abstractmethod
    def _run_restore(self, args: dict) -> None:
        pass

    @abstractmethod
    def _dry_run_restore(self, args: dict) -> None:
        pass

    def run_restore(self) -> None:
        args = self._prepare_run_restore()
        if self._dry_run is True:
            self._dry_run_restore(args)
        else:
            self._run_restore(args)
