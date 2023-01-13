import locale
import logging
import os
import shutil
from pathlib import Path

import pytest
from assertpy import assert_that
from freezegun import freeze_time

from src.bashckup.bashckup import main

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Change working directory to test folder
"""


@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)


@pytest.fixture(autouse=True)
def output_folder():
    output_path = current_path / 'output'
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


"""
Test too many things in one test
"""


@freeze_time('2023-07-10 15:02:10')
def test_tar_gz_clean(output_folder):
    # Given
    config_file = current_path / 'confs' / 'tar-gz-clean.yml'
    expected_output_folder = output_folder / 'tar-gz-clean'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).is_length(2)
    snar_file = list(filter(lambda f: f['file-name'].endswith('.snar'), output))[0]
    bck_file = list(filter(lambda f: f['file-name'].endswith('.tar.gz'), output))[0]
    assert_that(snar_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-snap-w28.snar')
    assert_that(snar_file['size']).is_between(99, 100)

    assert_that(bck_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-gz-clean.tar.gz')
    assert_that(bck_file['size']).is_between(200, 210)


@freeze_time('2023-07-10 15:02:10')
def test_tar_gz_clean_verbose(caplog, output_folder):
    caplog.set_level(logging.DEBUG)
    # Given
    config_file = current_path / 'confs' / 'tar-gz-clean.yml'
    # When
    return_code = main(['--verbose', 'backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    assert any(record.levelno == logging.DEBUG for record in caplog.records)


"""
test quiet mode
"""


@freeze_time('2023-07-10 15:02:10')
def test_tar_gz_clean_quiet(caplog, output_folder):
    # Given
    config_file = current_path / 'confs' / 'tar-gz-clean.yml'
    # When
    return_code = main(['--quiet', 'backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    assert_that(caplog.records).is_empty()
