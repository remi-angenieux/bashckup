import argparse
import ast
import datetime
import logging
import sys
import time

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from yaml import Loader
from yaml.loader import SafeLoader

from src.actuators.actuators_factories import ActuatorFactory
from src.actuators.exceptions import UserException, RunningException

yaml_schema = """
type: array
items:
  type: object
  properties:
    name:
      type: string
    id:
      type: string
      pattern: '[a-zA-Z0-9]+'
    reader:
      type: object
      properties:
        module:
          type: string
        args:
          type: object
      required:
        - module
      additionalProperties: false
    transformers:
      type: array
      items:
        type:
          - object
          - string
        minProperties: 1
        maxProperties: 1
        patternProperties:
          '.*':
            type: object
            properties:
              args:
                type: object
                additionalProperties: true
            additionalProperties: false
        additionalProperties: false
    writer:
      type: object
      properties:
        module:
          type: string
        args:
          type: object
      required:
        - module
      additionalProperties: false
    post-backup:
      type: array
      items:
        type:
          - object
          - string
        minProperties: 1
        maxProperties: 1
        patternProperties:
          '.*':
            type: object
            properties:
              args:
                type: object
                additionalProperties: true
            additionalProperties: false
        additionalProperties: false
  required:
    - reader
    - writer
    - id
"""


class KeyValue(argparse.Action):
    # Constructor calling
    def __call__(self, parser, namespace,
                 values, option_string=None):
        setattr(namespace, self.dest, dict())

        for value in values:
            # split it into key and value
            key, value = value.split('=')
            # assign into dictionary
            getattr(namespace, self.dest)[key] = ast.literal_eval(value)


class AppendKeyValue(argparse.Action):
    noOperation = 'nop'

    # Constructor calling
    def __call__(self, parser, namespace,
                 values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        setattr(namespace, self.dest, items)

        dictionary = dict()
        if values != [self.noOperation]:
            for value in values:
                # split it into key and value
                key, value = value.split('=')
                # assign into dictionary
                dictionary[key] = ast.literal_eval(value)
        getattr(namespace, self.dest).append(dictionary)


def read_config_from_file(config_file: argparse.FileType):
    with config_file as f:
        config = yaml.load(f, Loader=SafeLoader)
    try:
        validate(config, yaml.load(yaml_schema, Loader=Loader))
    except ValidationError as e:
        raise UserException('Validation error on config file\n'
                            f'On property {e.json_path}\n'
                            f'Error description: {e.message}\n'
                            f'''Helper: {e.schema.get('description')}''') from None
    ids = list(map(lambda c: c['id'], config))
    if len(ids) != len(config):
        raise UserException('Backup id must be unique')
    return config


def read_config_from_cli(parameters: argparse.Namespace):
    result = []
    backup = {'name': 'Backup from CLI', 'id': '.',  # Id = . for file path, it prevents to add another folder
              'reader': {'module': parameters.reader_module, 'args': parameters.reader_args},
              'transformers': [],
              'writer': {'module': parameters.writer_module, 'args': parameters.writer_args},
              'post-backup': []}
    if parameters.transformer_module is not None or parameters.transformer_args is not None:
        if parameters.transformer_module is None or parameters.transformer_args is None or len(
                parameters.transformer_module) != len(parameters.transformer_args):
            raise UserException("Number of transformers doesn't match number of transformer's arguments!")
        for i, v in enumerate(parameters.transformer_module):
            m = parameters.transformer_module[i]
            args = parameters.transformer_args[i]
            module = {m: {'args': args}}
            backup['transformers'].append(module)
    if parameters.post_backup_module is not None or parameters.post_backup_args is not None:
        if parameters.post_backup_module is None or parameters.post_backup_args is None or len(
                parameters.post_backup_module) != len(parameters.post_backup_args):
            raise UserException("Number of post-backup doesn't match number of post-backup's arguments!\n")
        for i, v in enumerate(parameters.post_backup_module):
            m = parameters.post_backup_module[i]
            args = parameters.post_backup_args[i]
            module = {m: {'args': args}}
            backup['post-backup'].append(module)
    result.append(backup)
    return result


def prepare(global_parameters: dict, configurations: dict) -> dict:
    result = {}
    for current_backup in configurations:
        metadata = {}
        modules = {}

        global_context = {**global_parameters, **{'backup-id': current_backup['id']}}

        reader = ActuatorFactory().build_reader(global_context, current_backup['reader'], metadata)
        modules.update({'reader': reader})
        metadata.update(reader.prepare_module())

        if current_backup.get('transformers') is not None:
            for transformer in current_backup['transformers']:
                trans = ActuatorFactory().build_transformer(global_context, transformer, metadata)
                transformers = modules.get('transformers', [])
                transformers.append(trans)
                modules.update({'transformers': transformers})
                metadata.update(trans.prepare_module())

        writer = ActuatorFactory().build_writer(global_context, current_backup['writer'], metadata)
        modules.update({'writer': writer})
        metadata.update(writer.prepare_module())

        if current_backup.get('post-backup') is not None:
            for post_backup in current_backup['post-backup']:
                post_bck = ActuatorFactory().build_post_backup(global_context, post_backup, metadata)
                post_backups = modules.get('post-backup', [])
                post_backups.append(post_bck)
                modules.update({'post-backup': post_backups})
                metadata.update(post_bck.prepare_module())

        result.update({current_backup['id']: {'modules': modules, 'metadata': metadata}})

    return result


"""
:returns: True if no errors appear during the backup, otherwise False.
"""


def run_backup_plans(global_parameters: dict, backup_plans: dict) -> bool:
    error = False
    for (backup_id, backup_plan) in backup_plans.items():
        try:
            logging.info('=== Backup %s ===', backup_id)

            #
            # Backup
            #
            if global_parameters['dry-run'] is False:
                processes = []  # Store all processes to be able to retrieve errors
                try:
                    logging.info('= Run reader %s =', backup_plan['modules']['reader'].module_name())
                    processes.append(backup_plan['modules']['reader'].generate_backup_process())
                    if backup_plan['modules'].get('transformers') is not None:
                        for transformer in backup_plan['modules']['transformers']:
                            logging.info('= Run transformer %s =', transformer.module_name())
                            previous_process = processes[-1]
                            processes.append(transformer.generate_backup_process(previous_process.stdout))
                            previous_process.stdout.close()  # Allow previous process to receive a SIGPIPE

                    previous_process = processes[-1]
                    logging.info('= Run writer %s =', backup_plan['modules']['writer'].module_name())
                    processes.append(backup_plan['modules']['writer'].generate_backup_process(previous_process.stdout))
                    previous_process.stdout.close()  # Allow previous process to receive a SIGPIPE
                finally:
                    for process in processes:
                        return_code = process.wait()
                        if return_code != 0:
                            error = True
                            logging.error('ERROR: Error during execution of backup\n'
                                          f'Command output: {process.stderr.read().decode(sys.getdefaultencoding())}\n'
                                          f'''Command executed: {' '.join(process.args)}'''
                                          f'Error code: {return_code}')
                        else:
                            stderr = process.stderr.read().decode(sys.getdefaultencoding())
                            if stderr != '':
                                logging.debug(stderr)
                        if process.stderr is not None:
                            process.stderr.close()
                        if process.stdout is not None:
                            process.stdout.close()
            else:
                cmd = []
                cmd.extend(backup_plan['modules']['reader'].generate_dry_run_backup_cmd())
                if backup_plan['modules'].get('transformers') is not None:
                    for transformer in backup_plan['modules']['transformers']:
                        cmd.append('|')
                        cmd.extend(transformer.generate_dry_run_backup_cmd())

                cmd.append('|')
                cmd.extend(backup_plan['modules']['writer'].generate_dry_run_backup_cmd())
                logging.info(f'''Command [{' '.join(cmd)}] would have been ran.''')
            #
            # Post backup
            #
            if backup_plan['modules'].get('post-backup') is not None:
                logging.info('== Post backup ==')
                for post_backup in backup_plan['modules']['post-backup']:
                    logging.info('= Run post backup %s =', post_backup.module_name())
                    post_backup.run_backup()
        except (UserException, RunningException) as e:
            error = True
            logging.error(str(e))
    return error


def extract_cli_parameters(args):
    args_parser = argparse.ArgumentParser(prog='Backuper', description='Command line interface to backup everything!')
    args_parser.add_argument('--dry-run', action='store_true',
                             help='Run program in dry mode, nothing is done on the system')
    args_parser.add_argument('--verbose', action='store_true',
                             help='Run program in verbose mode to have all information printed on stdout. '
                                  'Cannot be used together with --quiet')
    args_parser.add_argument('--quiet', action='store_true',
                             help='Never print into stdout, only warning and errors will be printed in stderr. '
                                  'Cannot be used together with --verbose')

    sub_parser = args_parser.add_subparsers(title='Mode', dest='mode', required=True,
                                            description='Backup or restore')
    backup_parser = sub_parser.add_parser('backup', help='Get config by CLI arguments')
    restore_parser = sub_parser.add_parser('restore', help='Get config from a YAML file')

    for parse in [backup_parser, restore_parser]:
        sub_parser = parse.add_subparsers(title='Config mode', dest='config_mode', required=True,
                                          description='How backup rules are defined')
        cli_parser = sub_parser.add_parser('cli', help='Get config by CLI arguments')
        file_parser = sub_parser.add_parser('file', help='Get config from a YAML file')
        file_parser.add_argument('--config-file', type=argparse.FileType('r'), required=True,
                                 help='Config wile to read')
        cli_parser.add_argument('--reader-module', choices=ActuatorFactory.reader_module_name(), required=True,
                                help='Module used to generate source backup')
        cli_parser.add_argument('--reader-args', action=KeyValue, nargs='*', help='Arguments for the reader module')
        cli_parser.add_argument('--transformer-module', choices=ActuatorFactory.transformer_module_name(),
                                action='append',
                                help='Module to transform backup, order may be used to create transformation chain')
        cli_parser.add_argument('--transformer-args', action=AppendKeyValue, nargs='*',
                                help='Arguments for the transform module. Number of args must match number of transforms, '
                                     'you can use nop as empty arg')
        cli_parser.add_argument('--writer-module', choices=ActuatorFactory.writer_module_name(), required=True,
                                help='Module used to generate source backup')
        cli_parser.add_argument('--writer-args', action=KeyValue, nargs='*', help='Arguments for the writer module')
        cli_parser.add_argument('--post-backup-module', choices=ActuatorFactory.post_backup_module_name(),
                                action='append',
                                help='Module to some tasks after backup is done')
        cli_parser.add_argument('--post-backup-args', action=AppendKeyValue, nargs='*',
                                help='Arguments for the post-backup module. Number of args must match number of '
                                     'post-backup, you can use nop as empty arg')
    parameters = args_parser.parse_args(args)

    # Checks some basics stuff
    if parameters.verbose is True and parameters.quiet is True:
        raise UserException("--verbose and --quiet cannot present together, choose one.")

    return parameters


def configure_logging(parameters):
    error_stream_handler = logging.StreamHandler(sys.stderr)
    error_stream_handler.setLevel(logging.WARNING)
    handlers = [error_stream_handler]
    if parameters.quiet is False:
        msg_stream_handler = logging.StreamHandler(sys.stdout)
        if parameters.verbose is True:
            msg_stream_handler.setLevel(logging.DEBUG)
        else:
            msg_stream_handler.setLevel(logging.INFO)
        handlers.append(msg_stream_handler)
    logging.basicConfig(format='%(levelname)s - %(message)s', handlers=handlers, level=logging.DEBUG)


def main(args=None):
    starting_time = time.time()
    try:
        parameters = extract_cli_parameters(args)

        configure_logging(parameters)
        global_parameters = {'dry-run': parameters.dry_run, 'verbose': parameters.verbose}

        if parameters.config_mode == 'file':
            configurations = read_config_from_file(parameters.config_file)
        elif parameters.config_mode == 'cli':
            configurations = read_config_from_cli(parameters)
        else:
            raise ValueError(f'Config mode {parameters.config_mode} is not handled')

        backup_plans = prepare(global_parameters, configurations)

        have_error = run_backup_plans(global_parameters, backup_plans)
        if have_error is True:
            exit(1)
        return 0
    except Exception as e:
        logging.error(str(e))
        exit(1)
    finally:
        if logging.getLogger().isEnabledFor(logging.INFO):
            time_elapsed = datetime.timedelta(seconds=time.time() - starting_time)
            logging.info('Backups took %s', str(time_elapsed))


if __name__ == "__main__":
    main()
