import locale
import os
import shutil
from pathlib import Path

from _pytest.fixtures import fixture
from assertpy import assert_that
from freezegun import freeze_time

from bashckup.bashckup import main

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..' / '..'
conf_path = tests_path / 'resources' / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Depends on TAR and MARIADB tests
"""


@freeze_time('2023-07-10 15:02:10')
def test_mariadb_gz(output_folder):
    """
    GOAL: Test GZIP with default options (no args)
    """
    # Given
    config_file = conf_path / 'mariadb-gz.yml'
    expected_output_folder = output_folder / 'mariadb-gz'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).is_length(1)
    assert_that(output[0]['file-name']).is_equal_to('2023-07-10T15:02:10-mariadb-gz.sql.gz')
    # Info: Without compression its 10240 octets
    assert_that(output[0]['size']).is_between(9000, 9200)


@freeze_time('2023-07-10 15:02:10')
def test_tar_gz(output_folder):
    """
    GOAL: Test GZIP with custom option (level set to 9)
    """
    # Given
    config_file = conf_path / 'tar-gz.yml'
    expected_output_folder = output_folder / 'tar-gz'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).is_length(1)
    bck_file = output[0]
    assert_that(bck_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-gz.tar.gz')
    # With level set to 9 and same files, output size change a lot between executions
    # Info: Without compression its 10240 octets
    assert_that(bck_file['size']).is_between(160, 210)
