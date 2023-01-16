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
tests_path = current_path / '..'
conf_path = tests_path / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


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
