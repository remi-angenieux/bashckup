class RunningException(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return '\033[91m' + f'ERROR:\n' \
                            f'Reason: {self.message}'


class UserException(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return '\033[91m' + f'ERROR:\n' \
                            f'Reason: {self.message}'


class BackupException(UserException):
    def __init__(self, message: str, backup_id: str):
        super().__init__(message)
        self.backup_id = backup_id

    def __str__(self):
        return '\033[91m' + f'ERROR: On the [{self.backup_id}] backup\n' \
                            f'Reason: {self.message}'


class ModuleException(BackupException):
    def __init__(self, message: str, backup_id: str, module: str):
        super().__init__(message, backup_id)
        self.module = module

    def __str__(self):
        return '\033[91m' + f'ERROR: On the [{self.backup_id}] backup\n' \
                            f'On the [{self.module}] module\n' \
                            f'Reason: {self.message}'


class ParameterException(ModuleException):
    def __init__(self, message: str, parameter: str, backup_id: str, module: str):
        super().__init__(message, backup_id, module)
        self.parameter = parameter

    def __str__(self):
        return '\033[91m' + f'ERROR: On the [{self.module}] module\n' \
                            f'Validation error on parameter: {self.parameter}\n' \
                            f'Reason: {self.message}'
