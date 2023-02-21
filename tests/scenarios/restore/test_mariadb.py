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
files_path = tests_path / 'resources' / 'mariadb'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


@freeze_time('2023-07-10 15:02:10')
def test_restore_mariadb(backup_folder):
    """
    GOAL: Test restoration: all modifications have to be reverted
    """
    # Given
    config_file = conf_path / 'mariadb.yml'
    expected_backup_folder = backup_folder / 'mariadb'
    os.makedirs(expected_backup_folder)

    # Do some modifications
    process = subprocess.run(['mysql', '-D', 'test', '-e', "INSERT INTO `MOCK_DATA` (`id`, `app_name`, `app_version`, "
                                                           "`color_theme`) VALUES ('1001', 'bashckup-test', '0.1.0', "
                                                           "'blouge'); "
                                                           "UPDATE `MOCK_DATA` SET `app_version` = '0.0.1' "
                                                           "WHERE id = '42'"])
    shutil.copyfile(files_path / '2023-07-10T15:02:10-mariadb.sql',
                    expected_backup_folder / '2023-07-10T15:02:10-mariadb.sql')
    if process.returncode != 0:
        raise Exception("Unable run mysql command")

    # When
    return_code = main(['restore', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)

    # Remove 'comments'
    regex = r"/\*![0-9]{5} ?(?:[^*]*)\*/(?:;)?\n?"
    process = subprocess.run(['mysqldump', '--compact', '--skip-extended-insert', 'test'], capture_output=True,
                             shell=False, text=True)
    sql_dump = re.sub(regex, '', process.stdout, 0, re.MULTILINE)
    expected = (tests_path / '..' / '.github' / 'images' / 'database.sql').read_text().replace('COLLATE utf8mb4_bin ',
                                                                                               '')
    assert_that(sql_dump.replace('COLLATE utf8mb4_bin ', '')).is_equal_to(expected)
