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
tests_path = current_path / '..' / '..'
conf_path = tests_path / 'resources' / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Depends on TAR tests
"""


@fixture
def change_crypt_password_file_rights():
    """ Change password file right and the reset to default """
    crypt_password_file = conf_path / 'crypt-password.pwd'
    file_stat = os.stat(crypt_password_file)
    file_mod = file_stat.st_mode
    file_owner = file_stat.st_uid
    file_group = file_stat.st_gid
    os.chmod(crypt_password_file, 0o600)
    os.chown(crypt_password_file, 0, 0)
    yield crypt_password_file
    os.chmod(crypt_password_file, file_mod)
    os.chown(crypt_password_file, file_owner, file_group)


@fixture
def change_crypt_password_file_with_good_rights_and_bad_owner():
    """ Change password file right and the reset to default """
    crypt_password_file = conf_path / 'crypt-password.pwd'
    file_stat = os.stat(crypt_password_file)
    file_mod = file_stat.st_mode
    file_owner = file_stat.st_uid
    file_group = file_stat.st_gid
    os.chmod(crypt_password_file, 0o600)
    os.chown(crypt_password_file, os.getuid() + 1, 0)
    yield crypt_password_file
    os.chmod(crypt_password_file, file_mod)
    os.chown(crypt_password_file, file_owner, file_group)


@fixture
def change_crypt_password_file_readable_for_group_and_good_owner():
    """ Change password file right and the reset to default """
    crypt_password_file = conf_path / 'crypt-password.pwd'
    file_stat = os.stat(crypt_password_file)
    file_mod = file_stat.st_mode
    file_owner = file_stat.st_uid
    file_group = file_stat.st_gid
    os.chmod(crypt_password_file, 0o660)
    os.chown(crypt_password_file, os.getuid(), 0)
    yield crypt_password_file
    os.chmod(crypt_password_file, file_mod)
    os.chown(crypt_password_file, file_owner, file_group)


@fixture
def change_crypt_password_file_readable_for_everyone_and_good_owner():
    """ Change password file right and the reset to default """
    crypt_password_file = conf_path / 'crypt-password.pwd'
    file_stat = os.stat(crypt_password_file)
    file_mod = file_stat.st_mode
    file_owner = file_stat.st_uid
    file_group = file_stat.st_gid
    os.chmod(crypt_password_file, 0o666)
    os.chown(crypt_password_file, os.getuid(), 0)
    yield crypt_password_file
    os.chmod(crypt_password_file, file_mod)
    os.chown(crypt_password_file, file_owner, file_group)


@freeze_time('2023-07-10 15:02:10')
def test_tar_crypt_password_readable_for_everyone(caplog,
                                                  change_crypt_password_file_readable_for_everyone_and_good_owner,
                                                  backup_folder, server_data_folder):
    """
    Goal: Test file permission check on password file
    """
    caplog.set_level(logging.DEBUG)
    # Given
    config_file = conf_path / 'tar-crypt.yml'
    # When
    with pytest.raises(SystemExit) as e:
        main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert e.type == SystemExit
    assert e.value.code == 1
    assert_that(caplog.record_tuples).contains(
        ('root', logging.ERROR, 'ERROR: On the [tar-crypt] backup\n'
                                'On the [crypt] module\n'
                                'Validation error on parameter: password-file\n'
                                'Reason: File [resources/confs/crypt-password.pwd] must not be readable from group '
                                'and from others'))


@freeze_time('2023-07-10 15:02:10')
def test_tar_crypt_password_owned_by_another_user(caplog, change_crypt_password_file_with_good_rights_and_bad_owner,
                                                  backup_folder, server_data_folder):
    """
    Goal: Test file owner check on password file
    """
    caplog.set_level(logging.DEBUG)
    # Given
    config_file = conf_path / 'tar-crypt.yml'
    # When
    with pytest.raises(SystemExit) as e:
        main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert e.type == SystemExit
    assert e.value.code == 1
    assert_that(caplog.record_tuples).contains(
        ('root', logging.ERROR, 'ERROR: On the [tar-crypt] backup\n'
                                'On the [crypt] module\n'
                                'Validation error on parameter: password-file\n'
                                'Reason: File [resources/confs/crypt-password.pwd] is not owned by current '
                                'user'))


@freeze_time('2023-07-10 15:02:10')
def test_tar_crypt_password_readable_for_group(caplog, change_crypt_password_file_readable_for_group_and_good_owner,
                                               backup_folder, server_data_folder):
    """
    Goal: Test file permission check on password file for group
    """
    caplog.set_level(logging.DEBUG)
    # Given
    config_file = conf_path / 'tar-crypt.yml'
    # When
    with pytest.raises(SystemExit) as e:
        main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert e.type == SystemExit
    assert e.value.code == 1
    assert_that(caplog.record_tuples).contains(
        ('root', logging.ERROR, 'ERROR: On the [tar-crypt] backup\n'
                                'On the [crypt] module\n'
                                'Validation error on parameter: password-file\n'
                                'Reason: File [resources/confs/crypt-password.pwd] must not be readable from group '
                                'and from others'))


@freeze_time('2023-07-10 15:02:10')
def test_tar_crypt_password(backup_folder, server_data_folder, change_crypt_password_file_rights):
    """
    GOAL: Test CRYPT
    """
    # Given
    config_file = conf_path / 'tar-crypt.yml'
    expected_backup_folder = backup_folder / 'tar-crypt'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_backup_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).is_length(1)
    bck_file = output[0]
    assert_that(bck_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-crypt.tar.crypt')
    # Info: Without encryption its 10240 octets
    assert_that(bck_file['size']).is_between(10240, 10280)

    actual = (expected_backup_folder / '2023-07-10T15:02:10-tar-crypt.tar.crypt').read_text(errors='ignore')
    assert_that(actual).starts_with('Salted__')
