import locale
import os

from assertpy import assert_that
from pathlib import Path

from bashckup.actuators.readers import FileReader
from bashckup.actuators.writers import FileWriter

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..'
conf_path = tests_path / 'resources' / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Change working directory to test folder
"""


def test_generate_dry_run_backup_cmd(backup_folder, server_data_folder):
    # Given
    global_context = {'backup-id': 'test', 'dry-run': True, 'verbose': True, 'backup': True}
    args = {'path': str(server_data_folder)}
    metadata = {}
    reader_module = FileReader(global_context, args, metadata)
    writer_module = FileWriter(global_context, {'file-name': 'test', 'path': str(backup_folder)}, metadata)

    # When
    metadata.update(reader_module.prepare_module())
    metadata.update(writer_module.prepare_module())
    result = reader_module.generate_dry_run_backup_cmd()

    # Then
    assert_that(result).is_length(4)
    assert_that(result[0]).is_equal_to('tar')
    assert_that(result[1]).is_equal_to('--verbose')
    assert_that(result[2]).is_equal_to('--create')
    assert_that(result[3]).ends_with('tests/ut/../testFolder')
