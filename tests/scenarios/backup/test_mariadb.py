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
conf_path = tests_path / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


@freeze_time('2023-07-10 15:02:10')
def test_mariadb(output_folder):
    """
    GOAL: Test mariadb dump
    """
    # Given
    config_file = conf_path / 'mariadb.yml'
    expected_output_folder = output_folder / 'mariadb'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name})

    assert_that(output).contains_only({'file-name': '2023-07-10T15:02:10-mariadb.sql'})

    # Check if dump is equal to what are inside the DB
    # Remove COLLATE because it's not present in same way one a newer version of mariadb
    actual = (expected_output_folder / '2023-07-10T15:02:10-mariadb.sql').read_text().replace('COLLATE utf8mb4_bin ',
                                                                                              '')
    expected = (tests_path / 'expected' / 'sqlDump.sql').read_text().replace('COLLATE utf8mb4_bin ', '')
    assert_that(actual).contains(expected)

    # FIXME Use it for restore
    # Remove 'comments'
    regex = r"/\*![0-9]{5} ?(?:[^*]*)\*/(?:;)?\n?"
    process = subprocess.run(['mysqldump', '--compact', '--skip-extended-insert', 'test'], capture_output=True,
                             shell=False, text=True)
    sql_dump = re.sub(regex, '', process.stdout, 0, re.MULTILINE)
    expected = (tests_path / '..' / '.github' / 'images' / 'database.sql').read_text().replace('COLLATE utf8mb4_bin ',
                                                                                               '')
    assert_that(sql_dump.replace('COLLATE utf8mb4_bin ', '')).is_equal_to(expected)
