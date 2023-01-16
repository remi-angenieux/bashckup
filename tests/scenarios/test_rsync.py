import locale
import logging
import os
import shutil
from pathlib import Path

import pytest
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


@fixture
def change_user1_password_file_rights():
    """ Change password file right and the reset to default """
    user1_password_file = conf_path / 'user1.pwd'
    file_stat = os.stat(user1_password_file)
    file_mod = file_stat.st_mode
    file_owner = file_stat.st_uid
    file_group = file_stat.st_gid
    os.chmod(user1_password_file, 0o600)
    os.chown(user1_password_file, 0, 0)
    yield user1_password_file
    os.chmod(user1_password_file, file_mod)
    os.chown(user1_password_file, file_owner, file_group)


@freeze_time('2023-07-10 15:02:10')
def test_tar_rsync_password_readable_for_everyone(caplog, output_folder):
    """
    Goal: Test file permission check on password file
    """
    caplog.set_level(logging.DEBUG)
    # Given
    config_file = conf_path / 'tar-rsync.yml'
    expected_output_folder = output_folder / 'tar-rsync'
    # When
    with pytest.raises(SystemExit) as e:
        main(['backup', 'file', '--config-file', str(config_file)])
    assert e.type == SystemExit
    assert e.value.code == 1

    # Then
    assert_that(caplog.record_tuples).contains(
        ('root', logging.ERROR, 'password-file [confs/user1.pwd] must not be readable from group and from others'))


@freeze_time('2023-07-10 15:02:10')
def test_tar_rsync(change_user1_password_file_rights, output_folder):
    """
    Goal: Test RSYNC
    """
    # Given
    config_file = conf_path / 'tar-rsync.yml'
    expected_output_folder = output_folder / 'tar-rsync'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)

    # Check on client side
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).contains_only({'file-name': '2023-07-10T15:02:10-tar-rsync.tar', 'size': 10240})
    # Check on server side
    output = []
    with os.scandir('/bck/folder1/tar-rsync') as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).contains_only({'file-name': '2023-07-10T15:02:10-tar-rsync.tar', 'size': 10240})
