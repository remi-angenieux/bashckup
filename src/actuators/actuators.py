import subprocess
from abc import abstractmethod
from typing import AnyStr, IO

from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from src.actuators.exceptions import ParameterException


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
                   'additionalProperties': False}
               }

    def __init__(self, metadata: dict):
        validate(metadata, self._schema)
        self.__dict__.update(metadata)

    def get(self, key):
        return self.__dict__.get(key)


class AbstractActuator:
    def __init__(self, global_context: dict, args: dict, metadata: dict[str, dict[str, ActuatorMetadata]] = None):
        self._backup_id = global_context['backup-id']
        self._dry_run = global_context['dry-run']
        self._args: dict = args
        self._metadata: dict[str, dict[str, ActuatorMetadata]] = metadata

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

    """
    If an actuator needs to create something before running the backup plan, you can use this method
    """

    def _pre_run_tasks(self) -> None:
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

    """
    Do validation then run pre task and finally init metadata
    """

    def prepare_module(self):
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

    def generate_backup_process(self, stdin: IO[AnyStr], stdout: IO[AnyStr]) -> subprocess.Popen[str]:
        if self._dry_run is True:
            raise Exception('You are not allowed to call this function in dry-run')
        return subprocess.Popen(self._generate_backup_cmd(), shell=False, stdin=stdin, stdout=stdout,
                                stderr=subprocess.PIPE)


class PythonActuator(AbstractActuator):
    @abstractmethod
    def _prepare_run_backup(self) -> dict:
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
