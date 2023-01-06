import os
import subprocess
from abc import ABC
from pathlib import Path
from typing import IO, AnyStr

from jsonschema.validators import validate

from src.actuators.actuators import CommandActuator
from src.actuators.exceptions import ParameterException


class AbstractTransformer(CommandActuator, ABC):

    def _actuator_type(self) -> str:
        return 'transformer'

    def generate_backup_process(self, stdin: IO[AnyStr], stdout: IO[AnyStr] = subprocess.PIPE) \
            -> subprocess.Popen[str]:
        return super().generate_backup_process(stdin, stdout)


class GzipTransformer(AbstractTransformer):
    defaultLevel = 6
    validation_schema = {'type': 'object',
                         'properties': {
                             'level': {
                                 'type': 'integer',
                                 'minimum': 1,
                                 'maximum': 9,
                                 'default': defaultLevel,
                                 'description': 'Regulate the speed of compression using the specified digit #, '
                                                'where 1 indicates the fastest compression method (less compression) '
                                                'and 9 indicates the slowest compression method (best compression). '
                                                'The default compression level is ' + str(
                                     defaultLevel) + ' (that is, biased towards high compression at expense of speed).'}
                         },
                         'additionalProperties': False}

    @staticmethod
    def module_name() -> str:
        return 'gzip'

    def _get_params(self) -> None:
        validate(self._args, self.validation_schema)

        self.level = self._args.get('level', self.defaultLevel)

    def _generate_backup_cmd(self) -> [str]:
        cmd = ['gzip', '-' + str(self.level)]
        return cmd


class OpenSSLTransformer(AbstractTransformer):
    defaultLevel = 6
    validation_schema = {'type': 'object',
                         'properties': {
                             'password-file': {
                                 'type': 'string',
                                 'description': 'Path to the file that contains the password'}
                         },
                         'required': ['password-file'],
                         'additionalProperties': False}

    @staticmethod
    def module_name() -> str:
        return 'crypt'

    def _get_params(self) -> None:
        validate(self._args, self.validation_schema)

        password_file = Path(self._args['password-file'])
        if not password_file.is_file():
            raise ParameterException(f'''File [{self._args['password-file']}] doesn't exists''',
                                     'password-file', self._backup_id, self.module_name())
        if not os.access(password_file, os.R_OK):
            raise ParameterException(f'''File [{self._args['password-file']}] is not readable''', 'password-file',
                                     self._backup_id, self.module_name())
        if os.stat(password_file).st_mode & 0o77 != 0o0:
            raise ParameterException(f'''File [{self._args['password-file']}] must not be readable from group and '
                                                                              'from others''', 'password-file',
                                     self._backup_id, self.module_name())
        self.password_file = password_file

    def _generate_backup_cmd(self) -> [str]:
        cmd = ['openssl', 'enc', '-e', '-aes-256-cbc', '-pbkdf2', '-kfile', str(self.password_file)]
        return cmd
