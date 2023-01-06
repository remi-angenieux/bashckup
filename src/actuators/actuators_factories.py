from src.actuators.actuators import ActuatorMetadata
from src.actuators.post_backup import CleanFolderPostBackup, RsyncPostBackup, AbstractPostBackup
from src.actuators.readers import FileReader, MariaDBReader, AbstractReader
from src.actuators.transformers import GzipTransformer, OpenSSLTransformer, AbstractTransformer
from src.actuators.writers import FileWriter, AbstractWriter


class ActuatorFactory:
    readerModules = [FileReader, MariaDBReader]
    transformerModules = [GzipTransformer, OpenSSLTransformer]
    writerModules = [FileWriter]
    postBackupModules = [CleanFolderPostBackup, RsyncPostBackup]

    _reader = dict((x.module_name(), x.__name__) for x in readerModules)
    _transformers = dict((x.module_name(), x.__name__) for x in transformerModules)
    _writer = dict((x.module_name(), x.__name__) for x in writerModules)
    _post_backup = dict((x.module_name(), x.__name__) for x in postBackupModules)

    @staticmethod
    def reader_module_name() -> list[str]:
        return [x.module_name() for x in ActuatorFactory.readerModules]

    @staticmethod
    def transformer_module_name() -> list[str]:
        return [x.module_name() for x in ActuatorFactory.transformerModules]

    @staticmethod
    def writer_module_name() -> list[str]:
        return [x.module_name() for x in ActuatorFactory.writerModules]

    @staticmethod
    def post_backup_module_name() -> list[str]:
        return [x.module_name() for x in ActuatorFactory.postBackupModules]

    def build_reader(self, global_context: dict, config: dict,
                     metadata: dict[str, dict[str, ActuatorMetadata]]) -> AbstractReader:
        module_class_name = self._reader.get(config['module'])
        if module_class_name is None:
            raise ValueError(f'''Module {config['module']} is not managed''')
        else:
            return globals()[module_class_name](global_context, config['args'], metadata)

    def build_transformer(self, global_context: dict, config: dict or str,
                          metadata: dict[str, dict[str, ActuatorMetadata]]) -> AbstractTransformer:
        if type(config) is dict:
            module_name = next(iter(config))
            args = config[module_name]['args']
        elif type(config) is str:
            module_name = config
            args = {}
        else:
            raise Exception(f'Type {type(config).__name__} is not handled')
        module_class_name = self._transformers.get(module_name)
        if module_class_name is None:
            raise ValueError(f'Module {module_name} is not managed')
        else:
            return globals()[module_class_name](global_context, args, metadata)

    def build_writer(self, global_context: dict, config: dict,
                     metadata: dict[str, dict[str, ActuatorMetadata]]) -> AbstractWriter:
        module_class_name = self._writer.get(config['module'])
        if module_class_name is None:
            raise ValueError(f'''Module {config['module']} is not managed''')
        else:
            return globals()[module_class_name](global_context, config['args'], metadata)

    def build_post_backup(self, global_context: dict, config: dict or str,
                          metadata: dict[str, dict[str, ActuatorMetadata]]) -> AbstractPostBackup:
        if type(config) is dict:
            module_name = next(iter(config))
            args = config[module_name]['args']
        elif type(config) is str:
            module_name = config
            args = {}
        else:
            raise Exception(f'Type {type(config).__name__} is not handled')
        module_class_name = self._post_backup.get(module_name)
        if module_class_name is None:
            raise ValueError(f'Module {module_name} is not managed')
        else:
            return globals()[module_class_name](global_context, args, metadata)