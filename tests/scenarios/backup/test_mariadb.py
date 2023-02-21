import locale
import os
import re
import shutil
import subprocess
from pathlib import Path

from _pytest.fixtures import fixture
from assertpy import assert_that
from freezegun import freeze_time

from bashckup.bashckup import main

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..' / '..'
conf_path = tests_path / 'resources' / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


@freeze_time('2023-07-10 15:02:10')
def test_mariadb(backup_folder):
    """
    GOAL: Test mariadb dump
    """
    # Given
    config_file = conf_path / 'mariadb.yml'
    expected_backup_folder = backup_folder / 'mariadb'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_backup_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name})

    assert_that(output).contains_only({'file-name': '2023-07-10T15:02:10-mariadb.sql'})

    # Check if dump is equal to what are inside the DB
    # Remove COLLATE because it's not present in same way one a newer version of mariadb
    actual = (expected_backup_folder / '2023-07-10T15:02:10-mariadb.sql').read_text().replace('COLLATE utf8mb4_bin ',
                                                                                              '')
    expected = (tests_path / 'resources' / 'mariadb' / 'sqlDump.sql').read_text().replace('COLLATE utf8mb4_bin ', '')
    assert_that(actual).contains(expected)
