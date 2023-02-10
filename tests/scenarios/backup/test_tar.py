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
conf_path = tests_path / 'confs'
files_path = tests_path / 'files'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


@freeze_time('2023-07-10 15:02:10')
def test_tar(output_folder):
    """
    Goal: Test tar without differential options
    """
    # Given
    config_file = conf_path / 'tar.yml'
    expected_output_folder = output_folder / 'tar'
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).contains_only({'file-name': '2023-07-10T15:02:10-tar.tar', 'size': 10240})


@freeze_time('2023-07-10 15:02:10')
def test_differential_tar(output_folder):
    """
    GOAL: Test TAR with differential options, first backup
    """
    # Given
    config_file = conf_path / 'tar-diff.yml'
    expected_output_folder = output_folder / 'tar-diff'
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
    bck_file = list(filter(lambda f: f['file-name'].endswith('.tar'), output))[0]
    assert_that(snar_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-snap-w28.snar')
    assert_that(snar_file['size']).is_between(80, 100)

    assert_that(bck_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-diff.tar')
    assert_that(bck_file['size']).is_equal_to(10240)


@freeze_time('2023-07-10 15:02:10')
def test_differential_tar_incremental_backup(output_folder):
    """
    GOAL: Test TAR with differential options, incremental backup. File 2 is not present in initial archive
    """
    # Given
    config_file = conf_path / 'tar-diff.yml'
    expected_output_folder = output_folder / 'tar-diff'
    os.mkdir(expected_output_folder)
    shutil.copyfile(files_path / '2023-07-09T12:03:34-tar-snap-w28.snar',
                    expected_output_folder / '2023-07-09T12:03:34-tar-snap-w28.snar')
    shutil.copyfile(files_path / '2023-07-09T12:03:34-tar-diff.tar',
                    expected_output_folder / '2023-07-09T12:03:34-tar-diff.tar')
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name})

    assert_that(output).is_length(3)
    assert_that(output).contains_only(
        {'file-name': '2023-07-09T12:03:34-tar-snap-w28.snar'},
        {'file-name': '2023-07-09T12:03:34-tar-diff.tar'},
        {'file-name': '2023-07-10T15:02:10-tar-diff.tar'}
    )
