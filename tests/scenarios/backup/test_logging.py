import locale
import logging
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


# FIXME this test has to be rewritten
@freeze_time('2023-07-10 15:02:10')
def test_tar_gz_verbose(caplog, output_folder):
    """
    GOAL: Test verbose mode (it has to be tested on every reader and post-backup)
    """
    caplog.set_level(logging.DEBUG)
    # Given
    config_file = conf_path / 'tar-gz.yml'
    # When
    return_code = main(['--verbose', 'backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    assert any(record.levelno == logging.DEBUG for record in caplog.records)


# FIXME this test has to be rewritten
@freeze_time('2023-07-10 15:02:10')
def test_tar_gz_quiet(caplog, output_folder):
    """
    GOAL: Test quiet mode
    """
    # Given
    config_file = conf_path / 'tar-gz.yml'
    # When
    return_code = main(['--quiet', 'backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    assert_that(caplog.records).is_empty()
