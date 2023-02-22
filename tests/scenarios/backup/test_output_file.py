import locale
import logging
import os
import shutil
from pathlib import Path

import pytest
from assertpy import assert_that
from freezegun import freeze_time

from bashckup.bashckup import main

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..' / '..'
conf_path = tests_path / 'resources' / 'confs'
files_path = tests_path / 'resources' / 'tar'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Depends on TAR
"""


@freeze_time('2023-07-10 15:02:10')
def test_output_file_permissions(backup_folder, server_data_folder):
    """
    Goal: Test permission of the output file
    """
    # Given
    config_file = conf_path / 'tar.yml'
    expected_backup_folder = backup_folder / 'tar'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_backup_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name})

    assert_that(output).contains_only({'file-name': '2023-07-10T15:02:10-tar.tar'})
    actual_permissions = oct(os.stat(expected_backup_folder / '2023-07-10T15:02:10-tar.tar').st_mode & 0o777)
    assert_that(actual_permissions).is_equal_to(oct(0o600))


@freeze_time('2023-07-10 15:02:10')
def test_output_file_file_already_exists(backup_folder, server_data_folder, caplog):
    """
    Goal: Test permission of the output file
    """
    # Given
    caplog.set_level(logging.ERROR)
    config_file = conf_path / 'tar.yml'
    expected_backup_folder = backup_folder / 'tar'
    os.mkdir(expected_backup_folder)
    with open(expected_backup_folder / '2023-07-10T15:02:10-tar.tar', 'w') as f:
        f.write('Already existing backup')
    # When
    with pytest.raises(SystemExit) as e:
        main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert e.type == SystemExit
    assert e.value.code == 1
    assert_that(caplog.record_tuples).contains(
        ('root', logging.ERROR, 'ERROR: On the [tar] backup\n'
                                'On the [outputFile] module\n'
                                'Reason: File [backup/tar/2023-07-10T15:02:10-tar.tar] already exists'))


@freeze_time('2023-07-10 15:02:10')
def test_output_file_file_snar_permissions(backup_folder, server_data_folder):
    """
    GOAL: Test permission of snar file
    """
    # Given
    config_file = conf_path / 'tar-diff.yml'
    expected_backup_folder = backup_folder / 'tar-diff'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_backup_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name})

    assert_that(output).is_length(2)
    snar_file = list(filter(lambda f: f['file-name'].endswith('.snar'), output))[0]
    bck_file = list(filter(lambda f: f['file-name'].endswith('.tar'), output))[0]
    assert_that(snar_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-snap-w28.snar')
    assert_that(oct(os.stat(expected_backup_folder / snar_file['file-name']).st_mode & 0o777)).is_equal_to(oct(0o600))

    assert_that(bck_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-diff.tar')
    assert_that(oct(os.stat(expected_backup_folder / bck_file['file-name']).st_mode & 0o777)).is_equal_to(oct(0o600))
