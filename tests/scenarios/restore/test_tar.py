import locale
import os
import shutil
from pathlib import Path

from assertpy import assert_that
from freezegun import freeze_time

from bashckup.bashckup import main

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..' / '..'
conf_path = tests_path / 'resources' / 'confs'
files_path = tests_path / 'resources' / 'tar'
server_data_folder = tests_path / 'serverData'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


@freeze_time('2023-07-10 15:02:10')
def test_restore_tar(backup_folder):
    """
    GOAL: 2023-07-10T15:02:10-tar.tar fil be used
    2023-07-10T15:02:12-unknownBackup.tar is more recent but not with the correct backup file name
    """
    # Given
    config_file = conf_path / 'tar.yml'
    expected_backup_folder = backup_folder / 'tar'
    try:
        os.makedirs(expected_backup_folder)
        os.makedirs(server_data_folder)

        shutil.copyfile(files_path / '2023-07-10T15:02:10-tar.tar',
                        expected_backup_folder / '2023-07-10T15:02:10-tar.tar')
        shutil.copyfile(files_path / '2023-07-10T15:02:12-unknownBackup.tar',
                        expected_backup_folder / '2023-07-10T15:02:12-unknownBackup.tar')
        # When
        return_code = main(['restore', 'file', '--config-file', str(config_file)])
        # return_code = main(['--dry-run', 'restore', 'file', '--config-file', str(config_file)])

        # Then
        assert_that(return_code).is_equal_to(0)
        output = []
        with os.scandir(server_data_folder) as it:
            entry: os.DirEntry
            for entry in it:
                output.append({'file-name': entry.name, 'size': entry.stat().st_size})

        assert_that(output).contains_only({'file-name': 'file1', 'size': 17}, {'file-name': 'file2', 'size': 17})
    finally:
        shutil.rmtree(server_data_folder, ignore_errors=True)


@freeze_time('2023-07-10 15:02:10')
def test_restore_tar_backup_folder_not_empty(backup_folder):
    """
    GOAL: Previous files are copied in a folder and restoration is done
    """
    # Given

    config_file = conf_path / 'tar.yml'
    expected_backup_folder = backup_folder / 'tar'
    backup_of_backup_folder = str(server_data_folder) + '-bck-2023-07-10T15:02:10'

    try:
        os.mkdir(expected_backup_folder)
        shutil.copyfile(files_path / '2023-07-10T15:02:10-tar.tar',
                        expected_backup_folder / '2023-07-10T15:02:10-tar.tar')
        os.makedirs(server_data_folder)
        with open(server_data_folder / 'brokenBackup.txt', "w") as file:
            file.write("This file has to be backup when restoration will be done")
        # When
        return_code = main(['restore', 'file', '--config-file', str(config_file)])

        # Then
        assert_that(return_code).is_equal_to(0)

        # Check backupFolder
        output = []
        with os.scandir(server_data_folder) as it:
            entry: os.DirEntry
            for entry in it:
                output.append({'file-name': entry.name, 'size': entry.stat().st_size})

        assert_that(output).contains_only({'file-name': 'file1', 'size': 17}, {'file-name': 'file2', 'size': 17})

        # Check backupFolder-bck
        output = []
        with os.scandir(backup_of_backup_folder) as it:
            entry: os.DirEntry
            for entry in it:
                output.append({'file-name': entry.name, 'size': entry.stat().st_size})

        assert_that(output).contains_only({'file-name': 'brokenBackup.txt', 'size': 56})
    finally:
        shutil.rmtree(backup_of_backup_folder, ignore_errors=True)
        shutil.rmtree(server_data_folder, ignore_errors=True)


@freeze_time('2023-07-10 15:02:10')
def test_restore_differential_tar_incremental_backup(backup_folder):
    """
    GOAL: Test restore a differential backup with an increment
    """
    # Given
    config_file = conf_path / 'tar-diff.yml'
    expected_backup_folder = backup_folder / 'tar-diff'
    try:
        shutil.copytree(files_path / 'differential', expected_backup_folder)
        os.makedirs(server_data_folder)

        # When
        return_code = main(['backup', 'file', '--config-file', str(config_file)])

        # Then
        assert_that(return_code).is_equal_to(0)
        output = []
        with os.scandir(server_data_folder) as it:
            entry: os.DirEntry
            for entry in it:
                output.append({'file-name': entry.name})

        assert_that(output).contains_only({'file-name': 'file1', 'size': 17}, {'file-name': 'file2', 'size': 17})
    finally:
        shutil.rmtree(server_data_folder)
