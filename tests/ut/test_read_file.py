import locale
import os
import shutil

import pytest
from _pytest.fixtures import fixture
from assertpy import assert_that
from pathlib import Path

from bashckup.actuators.readers import FileReader
from bashckup.actuators.writers import FileWriter

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..'
conf_path = tests_path / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Change working directory to test folder
"""


@fixture(autouse=True)
def change_test_dir(monkeypatch):
    """ Change working directory to test folder """
    monkeypatch.chdir(tests_path)


@fixture(autouse=True)
def output_folder():
    """ Create and remove a folder """
    output_path = tests_path / 'output'
    os.makedirs(output_path, exist_ok=True)
    yield output_path
    # Clear output folder
    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def test_generate_dry_run_backup_cmd(output_folder):
    # Given
    global_context = {'backup-id': 'test', 'dry-run': True, 'verbose': True}
    backup_folder = tests_path / 'testFolder'
    output_folder = tests_path / 'output'
    args = {'path': str(backup_folder)}
    metadata = {}
    reader_module = FileReader(global_context, args, metadata)
    writer_module = FileWriter(global_context, {'file-name': 'test', 'path': str(output_folder)}, metadata)

    # When
    metadata.update(reader_module.prepare_module())
    metadata.update(writer_module.prepare_module())
    result = reader_module.generate_dry_run_backup_cmd()

    # Then
    assert_that(result).is_length(4)
    assert_that(result[0]).is_equal_to('tar')
    assert_that(result[1]).is_equal_to('--verbose')
    assert_that(result[2]).is_equal_to('-c')
    assert_that(result[3]).ends_with('tests/ut/../testFolder')
