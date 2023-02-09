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


@freeze_time('2023-07-09 15:02:10')
def test_tar_clean(output_folder):
    """
    Goal: Test clean folder, file older than 2 days has to be removed
    """
    # Given
    config_file = conf_path / 'tar-clean.yml'
    expected_output_folder = output_folder / 'tar-clean'
    generate_file(expected_output_folder, '2023-07-08T15:02:10-tar.tar')  # Expected to be kept (Diff 1 day)
    generate_file(expected_output_folder,
                  '2023-07-08T15:02:11-tar.tar')  # Expected to be kept, less than 2 days (2 days minus 1 s)
    generate_file(expected_output_folder, '2023-07-07T15:02:10-tar.tar')  # Expected to be removed exactly 2 days
    generate_file(expected_output_folder, '2023-07-06T15:02:10-tar.tar')  # Expected to be removed, older than 3 days
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name, 'size': entry.stat().st_size})

    assert_that(output).contains_only({'file-name': '2023-07-09T15:02:10-tar-clean.tar', 'size': 10240},
                                      {'file-name': '2023-07-08T15:02:10-tar.tar', 'size': 7},
                                      {'file-name': '2023-07-07T15:02:11-tar.tar', 'size': 7})


@freeze_time('2023-07-09 15:02:10')
def test_tar_diff_clean_retention_less_than_level0_frequency(caplog, output_folder):
    """
    Goal: Test clean folder with a retention for 'cleanFolder' lower than the differential backup interval of tar
    3th of July is the first day of the current week
    """
    caplog.set_level(logging.WARNING)
    # Given
    config_file = conf_path / 'tar-diff-clean.yml'
    expected_output_folder = output_folder / 'tar-diff-clean'
    generate_file(expected_output_folder, '2023-07-08T15:02:10-tar.tar')  # Expected to be kept (Diff 1 day)
    generate_file(expected_output_folder,
                  '2023-07-07T15:02:11-tar.tar')  # Expected to be kept, less than 2 days (2 days minus 1 s)
    generate_file(expected_output_folder, '2023-07-07T15:02:10-tar.tar')  # Expected to be kept, because retention will be set to 7
    generate_file(expected_output_folder, '2023-07-06T15:02:10-tar.tar')  # Expected to be kept, because retention will be set to 7
    # When
    return_code = main(['backup', 'file', '--config-file', str(config_file)])

    # Then
    assert_that(return_code).is_equal_to(0)
    output = []
    with os.scandir(expected_output_folder) as it:
        entry: os.DirEntry
        for entry in it:
            output.append({'file-name': entry.name})

    assert_that(output).contains_only({'file-name': '2023-07-09T15:02:10-tar-diff-clean.tar'},
                                      {'file-name': '2023-07-09T15:02:10-tar-snap-w27.snar'},
                                      {'file-name': '2023-07-08T15:02:10-tar.tar'},
                                      {'file-name': '2023-07-07T15:02:11-tar.tar'},
                                      {'file-name': '2023-07-07T15:02:10-tar.tar'},
                                      {'file-name': '2023-07-06T15:02:10-tar.tar'})

    assert_that(caplog.record_tuples).contains(
        ('root', logging.WARNING, 'WARNING: retention [2] is lower than the minimum possible [7]. '
                                  'Retention value is override by the minimum'))


def generate_file(expected_output_folder, file_name):
    if not os.path.isdir(expected_output_folder):
        os.makedirs(expected_output_folder)
    with open(expected_output_folder / file_name, 'w') as f:
        f.write('content')
